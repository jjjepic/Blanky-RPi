import asyncio
import socket
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

try:
    from asyncua import Server, ua
except ImportError:
    Server = None
    ua = None

from blanky import opcua_service
from blanky.opcua_nodes import COMMAND_TO_NODE, RECEIVE_NAMESPACE_URI, RECEIVE_NODE_IDENTIFIERS
from tools.benchmark_opcua import _run


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@unittest.skipUnless(Server is not None, "asyncua is not installed")
class OPCUAIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.url = f"opc.tcp://127.0.0.1:{_free_port()}"
        self.server = Server()
        await self.server.init()
        self.server.set_endpoint(self.url)
        for index in range(2, 5):
            await self.server.register_namespace(f"http://blanky.test/namespace/{index}")
        receive_namespace = await self.server.register_namespace(RECEIVE_NAMESPACE_URI)
        self.assertEqual(receive_namespace, 5)
        self.received_nodes = {}
        for name, identifier in RECEIVE_NODE_IDENTIFIERS.items():
            node = await self.server.nodes.objects.add_variable(ua.NodeId(identifier, 5), name, False)
            await node.set_writable()
            self.received_nodes[name] = node
        for node_id in set(COMMAND_TO_NODE.values()):
            parsed = ua.NodeId.from_string(node_id)
            node = await self.server.nodes.objects.add_variable(parsed, f"command_{parsed.Identifier}", False)
            await node.set_writable()
        diagnostic = await self.server.nodes.objects.add_variable(ua.NodeId(100, 5), "diagnostic", False)
        await diagnostic.set_writable()
        for identifier in range(101, 105):
            sensor = await self.server.nodes.objects.add_variable(ua.NodeId(identifier, 5), f"sensor_{identifier}", False)
            await sensor.set_writable()
        await self.server.start()

    async def asyncTearDown(self):
        await self.server.stop()

    async def _wait_for(self, predicate, timeout=5):
        deadline = asyncio.get_running_loop().time() + timeout
        while not predicate():
            if asyncio.get_running_loop().time() > deadline:
                self.fail("Timed out waiting for OPC UA condition")
            await asyncio.sleep(0.05)

    async def test_command_pulse_and_feedback(self):
        with patch.object(opcua_service, "OPCUA_URL", self.url), patch.object(
            opcua_service, "OPCUA_PULSE_SECONDS", 0.1
        ):
            bridge = opcua_service.OPCUABridge()
        try:
            await self._wait_for(lambda: bridge.health()["feedback_active"])
            self.assertEqual(len(bridge.health()["received"]), 25)
            bridge.enqueue_command("START", source="test")
            await self._wait_for(lambda: bridge.health()["last_write_ms"] is not None)
            await self._wait_for(lambda: bridge.timing_records()[0]["write_ms"] is not None)
            await asyncio.sleep(0.15)
            self.assertFalse(await self.server.get_node("ns=4;i=2").read_value())
            await self.received_nodes["system_on"].write_value(True)
            await self._wait_for(lambda: bridge.health()["last_ack_ms"] is not None)
            self.assertEqual(bridge.timing_records()[0]["source"], "test")
            self.assertEqual(bridge.timing_records()[0]["ack_status"], "plc_signal")
        finally:
            await asyncio.to_thread(bridge.close)

    async def test_read_only_benchmark_uses_both_clients(self):
        args = SimpleNamespace(
            url=self.url,
            read_node="ns=5;i=2",
            write_node=None,
            samples=2,
            warmup=0,
            timeout=5,
            poll_interval=0.02,
        )
        rows = await asyncio.to_thread(lambda: asyncio.run(_run(args)))
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["library"] for row in rows}, {"opcua", "asyncua"})
        self.assertTrue(all(row["read_ms"] > 0 for row in rows))

    async def test_diagnostic_write_benchmark_uses_both_clients(self):
        args = SimpleNamespace(
            url=self.url,
            read_node="ns=5;i=2",
            write_node="ns=5;i=100",
            return_node="ns=5;i=100",
            samples=2,
            warmup=0,
            timeout=5,
            poll_interval=0.01,
        )
        rows = await asyncio.to_thread(lambda: asyncio.run(_run(args)))
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["write_ms"] > 0 and row["return_ms"] > 0 for row in rows))
        self.assertFalse(await self.server.get_node("ns=5;i=100").read_value())

    async def test_optional_sensor_nodes_are_read_without_guessing_ids(self):
        sensors = {
            "cyl_c_retracted": "ns=5;i=101",
            "cyl_c_advanced": "ns=5;i=102",
            "cyl_d_retracted": "ns=5;i=103",
            "cyl_d_advanced": "ns=5;i=104",
        }
        with patch.object(opcua_service, "OPCUA_URL", self.url), patch.object(
            opcua_service, "OPCUA_SENSOR_NODE_IDS", sensors
        ):
            bridge = opcua_service.OPCUABridge()
        try:
            await self._wait_for(lambda: bridge.health()["feedback_active"])
            self.assertEqual(len(bridge.health()["received"]), 29)
            await self.server.get_node("ns=5;i=102").write_value(True)
            await self._wait_for(lambda: bridge.health()["received"]["cyl_c_advanced"])
        finally:
            await asyncio.to_thread(bridge.close)

    async def test_missing_receive_namespace_does_not_block_commands(self):
        with patch.object(opcua_service, "OPCUA_URL", self.url), patch.object(
            opcua_service, "OPCUA_RECEIVE_NAMESPACE_URI", "http://missing.example/"
        ):
            bridge = opcua_service.OPCUABridge()
        try:
            await self._wait_for(lambda: bridge.health()["connected"])
            await self._wait_for(lambda: bool(bridge.health()["feedback_error"]))
            bridge.enqueue_command("START")
            await self._wait_for(lambda: bridge.health()["last_write_ms"] is not None)
            self.assertFalse(bridge.health()["feedback_active"])
        finally:
            await asyncio.to_thread(bridge.close)

    async def test_stale_command_is_not_replayed_to_plc(self):
        with patch.object(opcua_service, "OPCUA_URL", self.url):
            bridge = opcua_service.OPCUABridge()
        try:
            await self._wait_for(lambda: bridge.health()["connected"])
            bridge._queue.put_nowait(("START", "test", time.monotonic() - 6, self.url))
            await self._wait_for(lambda: bool(bridge.timing_records()))
            self.assertEqual(bridge.timing_records()[0]["ack_status"], "stale_or_endpoint_changed")
            self.assertFalse(await self.server.get_node("ns=4;i=2").read_value())
        finally:
            await asyncio.to_thread(bridge.close)


if __name__ == "__main__":
    unittest.main()
