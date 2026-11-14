"""Compare legacy opcua and asyncua against the same OPC UA server.

Default mode performs read-only round trips. Optional writes require a dedicated,
non-actuating diagnostic node and an explicit opt-in.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import importlib.metadata
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from blanky.opcua_nodes import COMMAND_LEVEL_FALLBACK, COMMAND_TO_NODE  # noqa: E402


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low = int(position)
    return ordered[low] + (ordered[min(low + 1, len(ordered) - 1)] - ordered[low]) * (position - low)


def _print_summary(rows: list[dict]):
    for library in ("opcua", "asyncua"):
        for metric in ("read_ms", "write_ms", "return_ms"):
            values = [float(row[metric]) for row in rows if row["library"] == library and row[metric] != ""]
            if values:
                print(
                    f"{library:8} {metric:9} n={len(values):3} "
                    f"mediana={statistics.median(values):7.2f} ms "
                    f"p95={_percentile(values, 0.95):7.2f} ms"
                )


def _typed_value(value: bool, variant_type, ua):
    if variant_type in (ua.VariantType.Int16, ua.VariantType.Int32, ua.VariantType.Int64):
        value = int(value)
    elif variant_type in (ua.VariantType.Float, ua.VariantType.Double):
        value = float(value)
    elif variant_type != ua.VariantType.Boolean:
        raise ValueError(f"Diagnostic write node must be Boolean or numeric, got {variant_type}")
    return ua.DataValue(ua.Variant(value, variant_type))


async def _run(args) -> list[dict]:
    try:
        from asyncua import Client as AsyncClient, ua as async_ua
        from opcua import Client as LegacyClient, ua as legacy_ua
    except ImportError as exc:
        raise SystemExit("Install both asyncua and opcua (requirements.txt + requirements-dev.txt).") from exc

    legacy = LegacyClient(args.url, timeout=args.timeout)
    modern = AsyncClient(args.url, timeout=args.timeout)
    rows = []
    connection_ms = {}
    versions = {
        "opcua": importlib.metadata.version("opcua"),
        "asyncua": importlib.metadata.version("asyncua"),
    }
    connected_legacy = False
    connected_modern = False
    try:
        connect_order = ("asyncua", "opcua") if getattr(args, "connect_first", "opcua") == "asyncua" else ("opcua", "asyncua")
        for library in connect_order:
            start = time.perf_counter()
            if library == "opcua":
                legacy.connect()
                connected_legacy = True
            else:
                await modern.connect()
                connected_modern = True
            connection_ms[library] = round((time.perf_counter() - start) * 1000, 3)
            print(f"{library} connection: {connection_ms[library]:.2f} ms")

        legacy_read = legacy.get_node(args.read_node)
        modern_read = modern.get_node(args.read_node)
        write_nodes = None
        if args.write_node:
            legacy_write = legacy.get_node(args.write_node)
            modern_write = modern.get_node(args.write_node)
            legacy_type = legacy_write.get_data_type_as_variant_type()
            modern_type = await modern_write.read_data_type_as_variant_type()
            write_nodes = (legacy_write, modern_write, legacy_type, modern_type)
            legacy_return = legacy.get_node(args.return_node)
            modern_return = modern.get_node(args.return_node)

        for index in range(-args.warmup, args.samples):
            order = ("opcua", "asyncua") if index % 2 == 0 else ("asyncua", "opcua")
            for library in order:
                row = {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "library": library,
                    "library_version": versions[library],
                    "python_version": sys.version.split()[0],
                    "sample": index + 1,
                    "connection_ms": connection_ms[library],
                    "poll_interval_ms": round(args.poll_interval * 1000, 3),
                    "read_ms": "", "write_ms": "", "return_ms": "",
                }
                start = time.perf_counter()
                if library == "opcua":
                    legacy_read.get_value()
                else:
                    await modern_read.read_value()
                row["read_ms"] = round((time.perf_counter() - start) * 1000, 3)

                if write_nodes:
                    if library == "opcua":
                        node, variant_type, return_node, ua = write_nodes[0], write_nodes[2], legacy_return, legacy_ua
                        read_return = return_node.get_value
                        write_value = node.set_value
                    else:
                        node, variant_type, return_node, ua = write_nodes[1], write_nodes[3], modern_return, async_ua
                        read_return = return_node.read_value
                        write_value = node.write_value

                    async def read_bool():
                        value = read_return()
                        return bool(await value) if library == "asyncua" else bool(value)

                    async def write_bool(value: bool):
                        result = write_value(_typed_value(value, variant_type, ua))
                        if library == "asyncua":
                            await result

                    if await read_bool():
                        raise RuntimeError("Return signal is already TRUE; refusing to send a command")
                    start = time.perf_counter()
                    try:
                        await write_bool(True)
                        row["write_ms"] = round((time.perf_counter() - start) * 1000, 3)
                        deadline = start + args.timeout
                        while not await read_bool():
                            if time.perf_counter() >= deadline:
                                raise TimeoutError(f"{library}: no return signal from diagnostic node")
                            await asyncio.sleep(args.poll_interval)
                        row["return_ms"] = round((time.perf_counter() - start) * 1000, 3)
                    finally:
                        await write_bool(False)
                    deadline = time.perf_counter() + args.timeout
                    while await read_bool():
                        if time.perf_counter() >= deadline:
                            raise TimeoutError("Return signal did not reset; stopping benchmark")
                        await asyncio.sleep(args.poll_interval)

                if index >= 0:
                    rows.append(row)
    finally:
        if connected_modern:
            await modern.disconnect()
        if connected_legacy:
            legacy.disconnect()
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="OPC UA server URL")
    parser.add_argument("--read-node", default="ns=0;i=2258", help="Read-only node, default: server time")
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--connect-first", choices=("opcua", "asyncua"), default="opcua")
    parser.add_argument("--poll-interval", type=float, default=0.02)
    parser.add_argument("--csv", type=Path, help="Optional per-sample CSV output")
    parser.add_argument("--write-node", help="Dedicated non-actuating test command node")
    parser.add_argument("--return-node", help="Dedicated test return node; must reset to FALSE")
    parser.add_argument("--allow-write", action="store_true", help="Explicitly allow diagnostic writes")
    args = parser.parse_args()
    if args.samples < 1 or args.warmup < 0 or args.timeout <= 0 or args.poll_interval <= 0:
        parser.error("samples/timeout/poll-interval must be positive; warmup must not be negative")
    if args.write_node or args.return_node or args.allow_write:
        if not (args.write_node and args.return_node and args.allow_write):
            parser.error("write tests require --write-node, --return-node and --allow-write")
        live_nodes = set(COMMAND_TO_NODE.values()) | {node for node, _ in COMMAND_LEVEL_FALLBACK.values()}
        if args.write_node in live_nodes:
            parser.error("Known Blanky actuator command nodes are forbidden for the benchmark")

    rows = asyncio.run(_run(args))
    _print_summary(rows)
    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=tuple(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved {len(rows)} samples to {args.csv}")


if __name__ == "__main__":
    main()
