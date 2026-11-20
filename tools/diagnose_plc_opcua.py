"""Read-only check of the OPC UA interface expected by Blanky.

This tool never writes to the PLC. Run it from the Raspberry Pi with the
Blanky virtual environment active, preferably before attempting a command.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from blanky.config import OPCUA_RECEIVE_NAMESPACE_URI, OPCUA_URL
from blanky.opcua_nodes import COMMAND_TO_NODE, RECEIVE_NODE_IDENTIFIERS


async def diagnose(url: str, receive_uri: str, *, system_only: bool = False) -> int:
    try:
        from asyncua import Client, ua
    except ImportError:
        print("ERRO: asyncua não está instalado neste ambiente Python.")
        return 2

    errors = 0
    try:
        async with Client(url=url, timeout=5) as client:
            print(f"Ligação OPC UA: {url}")
            namespaces = await client.get_namespace_array()
            for index, uri in enumerate(namespaces):
                print(f"  ns={index}: {uri}")

            if not system_only:
                print("\nNós de comando (apenas leitura de metadados):")
            commands = {} if system_only else COMMAND_TO_NODE
            for command, node_id in commands.items():
                try:
                    node = client.get_node(node_id)
                    name = await node.read_browse_name()
                    node_type = await node.read_data_type_as_variant_type()
                    if node_type != ua.VariantType.Boolean:
                        errors += 1
                        print(f"  ERRO {command:20} {node_id:14} {name.Name}: tipo {node_type}, esperado Bool")
                    else:
                        print(f"  OK  {command:20} {node_id:14} {name.Name}")
                except Exception as exc:
                    errors += 1
                    print(f"  ERRO {command:20} {node_id:14} {exc}")

            print(f"\nURI de retorno esperado: {receive_uri}")
            try:
                receive_index = namespaces.index(receive_uri)
            except ValueError as exc:
                print(f"  ERRO: namespace de retorno não disponível: {exc}")
                return 1

            print(f"  Índice atual: ns={receive_index}")
            values = {}
            for signal, identifier in RECEIVE_NODE_IDENTIFIERS.items():
                if system_only and signal not in {"system_on", "system_stopped"}:
                    continue
                node_id = f"ns={receive_index};i={identifier}"
                try:
                    value = await client.get_node(node_id).read_value()
                    if not isinstance(value, bool):
                        errors += 1
                        print(f"  ERRO {signal:24} {node_id:14} tipo {type(value).__name__}, esperado Bool")
                    else:
                        values[signal] = value
                        print(f"  OK  {signal:24} {node_id:14} {value}")
                except Exception as exc:
                    errors += 1
                    print(f"  ERRO {signal:24} {node_id:14} {exc}")
            if {"system_on", "system_stopped"} <= values.keys():
                if values["system_on"] == values["system_stopped"]:
                    print("\nEstado do sistema incerto: Sistema Ligado e Sistema Parado têm o mesmo valor.")
                else:
                    print("\nEstado lido: " + ("Ligado" if values["system_on"] else "Parado"))
    except Exception as exc:
        print(f"ERRO: não foi possível ligar ou ler o servidor: {exc}")
        return 1

    print(f"\nResultado: {errors} nó(s) em falta, inacessíveis ou com tipo inesperado.")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=OPCUA_URL, help="Endpoint OPC UA configurado no Blanky")
    parser.add_argument("--receive-uri", default=OPCUA_RECEIVE_NAMESPACE_URI)
    parser.add_argument("--system-only", action="store_true", help="Ler apenas Sistema Ligado e Sistema Parado")
    args = parser.parse_args()
    return asyncio.run(diagnose(args.url, args.receive_uri, system_only=args.system_only))


if __name__ == "__main__":
    raise SystemExit(main())
