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


async def diagnose(url: str, receive_uri: str) -> int:
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

            print("\nNós de comando (apenas leitura de metadados):")
            for command, node_id in COMMAND_TO_NODE.items():
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
                receive_index = await client.get_namespace_index(receive_uri)
            except Exception as exc:
                print(f"  ERRO: namespace de retorno não disponível: {exc}")
                return 1

            print(f"  Índice atual: ns={receive_index}")
            for signal, identifier in RECEIVE_NODE_IDENTIFIERS.items():
                node_id = f"ns={receive_index};i={identifier}"
                try:
                    value = await client.get_node(node_id).read_value()
                    if not isinstance(value, bool):
                        errors += 1
                        print(f"  ERRO {signal:24} {node_id:14} tipo {type(value).__name__}, esperado Bool")
                    else:
                        print(f"  OK  {signal:24} {node_id:14} {value}")
                except Exception as exc:
                    errors += 1
                    print(f"  ERRO {signal:24} {node_id:14} {exc}")
    except Exception as exc:
        print(f"ERRO: não foi possível ligar ou ler o servidor: {exc}")
        return 1

    print(f"\nResultado: {errors} nó(s) em falta, inacessíveis ou com tipo inesperado.")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=OPCUA_URL, help="Endpoint OPC UA configurado no Blanky")
    parser.add_argument("--receive-uri", default=OPCUA_RECEIVE_NAMESPACE_URI)
    args = parser.parse_args()
    return asyncio.run(diagnose(args.url, args.receive_uri))


if __name__ == "__main__":
    raise SystemExit(main())
