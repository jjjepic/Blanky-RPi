from __future__ import annotations

import queue
import threading
import time
from datetime import datetime
from typing import Optional

from blanky.config import OPCUA_ENABLED, OPCUA_PULSE_SECONDS, OPCUA_URL

try:
    from opcua import Client, ua
except Exception:  # pragma: no cover
    Client = None
    ua = None


# Mapeamento direto: comando interno -> node_id OPC-UA (ns=4).
COMMAND_TO_NODE = {
    "START": "ns=4;i=2",
    "STOP": "ns=4;i=3",
    "MODE_FAST": "ns=4;i=4",
    "MODE_IDEAL": "ns=4;i=5",
    "MODE_MANUAL": "ns=4;i=6",
    "MODE_UNSPEC": "ns=4;i=7",
    "MOTOR_1_ON": "ns=4;i=8",
    "MOTOR_2_ON": "ns=4;i=9",
    "MOTOR_3_ON": "ns=4;i=10",
    "CYL_A_EXTEND": "ns=4;i=11",
    "CYL_B_EXTEND": "ns=4;i=12",
    "CYL_C_EXTEND": "ns=4;i=13",
    "CYL_D_EXTEND": "ns=4;i=14",
    "GREEN_ON": "ns=4;i=15",
    "RED_ON": "ns=4;i=16",
    "ROBOT_TO_METAL": "ns=4;i=17",
    "ROBOT_TO_NONMETAL": "ns=4;i=18",
    "MOTOR_1_OFF": "ns=4;i=29",
    "MOTOR_2_OFF": "ns=4;i=40",
    "MOTOR_3_OFF": "ns=4;i=51",
    "CYL_A_RETRACT": "ns=4;i=62",
    "CYL_B_RETRACT": "ns=4;i=73",
    "GREEN_OFF": "ns=4;i=84",
    "RED_OFF": "ns=4;i=95",
}

# Na tua imagem nao aparecem OFF para Valve C e D.
# Fallback: escrever False no mesmo no de ON.
COMMAND_LEVEL_FALLBACK = {
    "CYL_C_RETRACT": ("ns=4;i=13", False),
    "CYL_D_RETRACT": ("ns=4;i=14", False),
}


class OPCUABridge:
    def __init__(self):
        self.enabled = bool(OPCUA_ENABLED and Client is not None and ua is not None)
        self._pulse_seconds = float(OPCUA_PULSE_SECONDS)
        self._url = str(OPCUA_URL)
        self._client: Optional[Client] = None
        self._lock = threading.Lock()
        self._queue: queue.Queue[str] = queue.Queue()

        self._connected = False
        self._last_error = ""
        self._last_write = ""
        self._last_command = ""

        if self.enabled:
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()

    def enqueue_command(self, command: str):
        if not self.enabled:
            return
        self._queue.put(command)

    def configure_connection(self, url: str):
        """Use a new OPC UA endpoint for the next queued command."""
        url = (url or OPCUA_URL).strip()
        if url == self._url:
            return
        self._url = url
        self._disconnect()

    def _worker_loop(self):
        while True:
            command = self._queue.get()
            try:
                self._ensure_connected()
                self._send_command(command)
            except Exception as exc:
                self._last_error = str(exc)
                self._disconnect()

    def _ensure_connected(self):
        with self._lock:
            if self._client is not None:
                self._connected = True
                return

            client = Client(self._url)
            client.connect()
            self._client = client
            self._connected = True
            self._last_error = ""

    def _disconnect(self):
        with self._lock:
            if self._client is not None:
                try:
                    self._client.disconnect()
                except Exception:
                    pass
            self._client = None
            self._connected = False

    def _send_command(self, command: str):
        self._last_command = command
        node_id = COMMAND_TO_NODE.get(command)
        if node_id:
            self._write_pulse(node_id, True)
            return

        fallback = COMMAND_LEVEL_FALLBACK.get(command)
        if fallback:
            fallback_node, level_value = fallback
            self._write_node_value(fallback_node, level_value)

    def _write_pulse(self, node_id: str, active_value):
        self._write_node_value(node_id, active_value)
        time.sleep(self._pulse_seconds)
        self._write_node_value(node_id, False)

    def _write_node_value(self, node_id: str, value):
        assert self._client is not None
        node = self._client.get_node(node_id)
        node_type = node.get_data_type_as_variant_type()

        if node_type in (ua.VariantType.Int16, ua.VariantType.Int32, ua.VariantType.Int64):
            cast_value = int(value)
        elif node_type in (ua.VariantType.Float, ua.VariantType.Double):
            cast_value = float(value)
        elif node_type == ua.VariantType.Boolean:
            cast_value = bool(value)
        else:
            cast_value = str(value)

        node.set_value(ua.DataValue(ua.Variant(cast_value, node_type)))
        self._last_write = f"{datetime.now().strftime('%H:%M:%S')} {node_id}={cast_value}"
        self._last_error = ""
        self._connected = True

    def health(self) -> dict:
        return {
            "enabled": self.enabled,
            "connected": self._connected,
            "url": self._url,
            "last_error": self._last_error,
            "last_write": self._last_write,
            "last_command": self._last_command,
        }


_BRIDGE: Optional[OPCUABridge] = None


def get_opcua_bridge() -> OPCUABridge:
    global _BRIDGE
    if _BRIDGE is None:
        _BRIDGE = OPCUABridge()
    return _BRIDGE
