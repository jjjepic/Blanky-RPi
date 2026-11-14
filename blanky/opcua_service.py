"""Asynchronous OPC UA transport for commands and PLC return signals."""

from __future__ import annotations

import asyncio
import queue
import threading
import time
from collections import deque
from datetime import datetime

from blanky.config import (
    OPCUA_ENABLED,
    OPCUA_PULSE_SECONDS,
    OPCUA_RECEIVE_NAMESPACE_URI,
    OPCUA_SENSOR_NODE_IDS,
    OPCUA_URL,
)
from blanky.opcua_nodes import (
    COMMAND_LEVEL_FALLBACK,
    COMMAND_TO_NODE,
    COMMAND_TO_RECEIVE_SIGNAL,
    RECEIVE_NODE_IDENTIFIERS,
)

try:
    from asyncua import Client, ua
except ImportError:  # Keep the UI usable when optional PLC packages are absent.
    Client = None
    ua = None


class _FeedbackHandler:
    def __init__(self, bridge: "OPCUABridge", names_by_node: dict[str, str]):
        self._bridge = bridge
        self._names_by_node = names_by_node

    def datachange_notification(self, node, value, data):
        name = self._names_by_node.get(str(node.nodeid))
        if name is not None:
            self._bridge._record_feedback(name, bool(value))

    def status_change_notification(self, status):
        self._bridge._set_feedback_error(f"Subscription status: {status}")


class OPCUABridge:
    def __init__(self):
        self.enabled = bool(OPCUA_ENABLED and Client is not None and ua is not None)
        self._pulse_seconds = float(OPCUA_PULSE_SECONDS)
        self._url = str(OPCUA_URL)
        self._receive_namespace_uri = str(OPCUA_RECEIVE_NAMESPACE_URI)
        self._sensor_node_ids = dict(OPCUA_SENSOR_NODE_IDS)
        self._lock = threading.Lock()
        self._queue: queue.Queue[tuple[str, str, float, str]] = queue.Queue(maxsize=100)
        self._stop = threading.Event()
        self._thread = None

        self._connected = False
        self._last_error = ""
        self._feedback_error = ""
        self._feedback_active = False
        self._feedback_mode = "unavailable"
        self._received: dict[str, bool] = {}
        self._last_feedback = ""
        self._last_write = ""
        self._last_command = ""
        self._last_write_ms: float | None = None
        self._last_ack_ms: float | None = None
        self._pending: dict[str, dict] = {}
        self._timings: deque[dict] = deque(maxlen=500)

        if self.enabled:
            self._thread = threading.Thread(target=self._thread_main, daemon=True, name="blanky-opcua")
            self._thread.start()

    def enqueue_command(self, command: str, source: str = "unknown"):
        if self.enabled and (command in COMMAND_TO_NODE or command in COMMAND_LEVEL_FALLBACK):
            with self._lock:
                endpoint = self._url
            try:
                self._queue.put_nowait((command, source, time.monotonic(), endpoint))
            except queue.Full:
                with self._lock:
                    self._last_error = f"{command}: OPC UA command queue is full"

    def configure_connection(self, url: str):
        url = (url or OPCUA_URL).strip()
        with self._lock:
            if url != self._url:
                self._url = url
                self._received.clear()
                self._feedback_active = False
                self._last_ack_ms = None

    def close(self):
        self._stop.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=6)

    def _thread_main(self):
        asyncio.run(self._run())

    async def _run(self):
        retry_seconds = 1.0
        while not self._stop.is_set():
            with self._lock:
                url = self._url
            client = None
            subscription = None
            try:
                client = Client(url=url, timeout=5)
                await client.connect()
                with self._lock:
                    self._connected = True
                    self._last_error = ""
                retry_seconds = 1.0
                subscription, feedback_nodes = await self._start_feedback(client)
                last_poll = time.monotonic()
                last_keepalive = time.monotonic()
                while not self._stop.is_set():
                    with self._lock:
                        endpoint_changed = self._url != url
                        feedback_mode = self._feedback_mode
                    if endpoint_changed:
                        break

                    try:
                        command, source, queued_at, queued_endpoint = self._queue.get_nowait()
                    except queue.Empty:
                        command = None
                    if command is not None:
                        age = time.monotonic() - queued_at
                        if age > 5.0 or queued_endpoint != url:
                            with self._lock:
                                self._timings.append({
                                    "time": datetime.now().isoformat(timespec="seconds"),
                                    "command": command, "source": source,
                                    "node": COMMAND_TO_NODE.get(command, ""),
                                    "library": "asyncua", "queue_ms": round(age * 1000, 2),
                                    "write_ms": None, "ack_ms": None,
                                    "ack_status": "stale_or_endpoint_changed",
                                })
                                self._last_error = f"{command}: stale command not sent"
                        else:
                            try:
                                await self._send_command(client, command, source, queued_at)
                            except Exception as exc:
                                with self._lock:
                                    self._last_error = f"{command}: {exc}"
                                raise

                    now = time.monotonic()
                    if feedback_mode == "polling" and now - last_poll >= 0.5:
                        await self._read_feedback(client, feedback_nodes)
                        last_poll = now
                        last_keepalive = now
                    if now - last_keepalive >= 5.0:
                        await client.get_node("i=2258").read_value()
                        last_keepalive = now
                    self._expire_pending(now)
                    await asyncio.sleep(0.05)
            except Exception as exc:
                with self._lock:
                    self._last_error = str(exc)
            finally:
                if subscription is not None:
                    try:
                        await subscription.delete()
                    except Exception:
                        pass
                if client is not None:
                    try:
                        await client.disconnect()
                    except Exception:
                        pass
                with self._lock:
                    self._connected = False
                    self._feedback_active = False
                    self._feedback_mode = "unavailable"
                    self._received.clear()
                    for record in self._pending.values():
                        record["ack_status"] = "disconnected"
                    self._pending.clear()
                    self._last_ack_ms = None
            if not self._stop.is_set():
                await asyncio.sleep(retry_seconds)
                retry_seconds = min(retry_seconds * 2, 10.0)

    async def _start_feedback(self, client):
        subscription = None
        try:
            namespace = await client.get_namespace_index(self._receive_namespace_uri)
            nodes = {
                name: client.get_node(f"ns={namespace};i={identifier}")
                for name, identifier in RECEIVE_NODE_IDENTIFIERS.items()
            }
            nodes.update({name: client.get_node(node_id) for name, node_id in self._sensor_node_ids.items()})
            subscription = await client.create_subscription(
                200, _FeedbackHandler(self, {str(node.nodeid): name for name, node in nodes.items()})
            )
            try:
                await subscription.subscribe_data_change(list(nodes.values()))
                with self._lock:
                    self._feedback_mode = "subscription"
                    self._feedback_error = ""
                    self._feedback_active = True
            except Exception:
                await subscription.delete()
                subscription = None
                with self._lock:
                    self._feedback_mode = "polling"
                    self._feedback_active = True
            await self._read_feedback(client, nodes)
            return subscription, nodes
        except Exception as exc:
            if subscription is not None:
                try:
                    await subscription.delete()
                except Exception:
                    pass
            self._set_feedback_error(str(exc))
            return None, {}

    async def _read_feedback(self, client, nodes: dict):
        if not nodes:
            return
        values = await client.read_values(list(nodes.values()))
        for name, value in zip(nodes, values):
            self._record_feedback(name, bool(value))
        with self._lock:
            self._feedback_active = True
            self._feedback_error = ""

    def _record_feedback(self, name: str, value: bool):
        now = time.monotonic()
        with self._lock:
            old_value = self._received.get(name)
            self._received[name] = value
            if old_value == value:
                return
            self._last_feedback = f"{datetime.now().strftime('%H:%M:%S')} {name}={int(value)}"
            pending = self._pending.pop(name, None) if value else None
            if pending is not None:
                latency = round((now - pending["started"]) * 1000, 2)
                pending["ack_ms"] = latency
                pending["ack_status"] = "plc_signal"
                self._last_ack_ms = latency

    def _set_feedback_error(self, message: str):
        with self._lock:
            self._feedback_error = message
            self._feedback_active = False
            self._feedback_mode = "polling"

    async def _send_command(self, client, command: str, source: str, queued_at: float):
        node_id = COMMAND_TO_NODE.get(command)
        fallback = COMMAND_LEVEL_FALLBACK.get(command)
        if node_id is None and fallback is None:
            return
        if fallback is not None:
            node_id, value = fallback
        else:
            value = True

        start = time.monotonic()
        signal = COMMAND_TO_RECEIVE_SIGNAL.get(command)
        record = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "command": command,
            "source": source,
            "node": node_id,
            "library": "asyncua",
            "queue_ms": round((start - queued_at) * 1000, 2),
            "write_ms": None,
            "ack_ms": None,
            "ack_status": "unavailable",
        }
        with self._lock:
            self._last_command = command
            self._last_ack_ms = None
            self._timings.append(record)
            if signal and self._feedback_active:
                old = self._pending.pop(signal, None)
                if old is not None:
                    old["ack_status"] = "superseded"
                record["started"] = start
                record["ack_status"] = "pending"
                self._pending[signal] = record

        try:
            await self._write_node_value(client, node_id, value)
            elapsed = round((time.monotonic() - start) * 1000, 2)
            with self._lock:
                record["write_ms"] = elapsed
                self._last_write_ms = elapsed
                self._last_write = f"{datetime.now().strftime('%H:%M:%S')} {node_id}={value}"
                self._last_error = ""
            if fallback is None:
                await asyncio.sleep(self._pulse_seconds)
                await self._write_node_value(client, node_id, False)
        except Exception:
            with self._lock:
                record["ack_status"] = "write_error"
                if signal and self._pending.get(signal) is record:
                    del self._pending[signal]
            raise

    async def _write_node_value(self, client, node_id: str, value: bool):
        node = client.get_node(node_id)
        node_type = await node.read_data_type_as_variant_type()
        if node_type in (ua.VariantType.Int16, ua.VariantType.Int32, ua.VariantType.Int64):
            cast_value = int(value)
        elif node_type in (ua.VariantType.Float, ua.VariantType.Double):
            cast_value = float(value)
        elif node_type == ua.VariantType.Boolean:
            cast_value = bool(value)
        else:
            cast_value = str(value)
        await node.write_value(ua.DataValue(ua.Variant(cast_value, node_type)))

    def _expire_pending(self, now: float):
        with self._lock:
            for name, record in list(self._pending.items()):
                if now - record["started"] >= 5.0:
                    record["ack_status"] = "timeout"
                    del self._pending[name]

    def timing_records(self) -> list[dict]:
        with self._lock:
            return [{key: value for key, value in item.items() if key != "started"} for item in self._timings]

    def health(self) -> dict:
        with self._lock:
            return {
                "enabled": self.enabled,
                "connected": self._connected,
                "url": self._url,
                "last_error": self._last_error,
                "feedback_error": self._feedback_error,
                "feedback_mode": self._feedback_mode,
                "feedback_active": self._feedback_active,
                "received": dict(self._received),
                "last_feedback": self._last_feedback,
                "last_write": self._last_write,
                "last_command": self._last_command,
                "last_write_ms": self._last_write_ms,
                "last_ack_ms": self._last_ack_ms,
            }


_BRIDGE: OPCUABridge | None = None


def get_opcua_bridge() -> OPCUABridge:
    global _BRIDGE
    if _BRIDGE is None:
        _BRIDGE = OPCUABridge()
    return _BRIDGE
