import asyncio
import socket
import types
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


def _run_without_io(coroutine):
    """Drive fake-only awaits without creating a Windows socket-backed loop."""
    while True:
        try:
            coroutine.send(None)
        except StopIteration as result:
            return result.value


def _data_value(value, status="Good"):
    return SimpleNamespace(Value=SimpleNamespace(Value=value),
                           StatusCode=SimpleNamespace(name=status, is_good=lambda: status == "Good"))


class OPCUAOfflineTests(unittest.TestCase):
    def test_stop_discards_commands_not_yet_written(self):
        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()
        bridge.enabled = bridge._connected = True
        bridge.enqueue_command("MOTOR_1_ON", "test")
        bridge.enqueue_command("STOP", "test")
        self.assertEqual(bridge.timing_records()[0]["ack_status"], "superseded_by_stop")
        self.assertEqual(bridge._queue.get_nowait()["command"], "STOP")

    def test_feedback_failure_invalidates_values_but_not_send_queue(self):
        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()
        bridge.enabled = bridge._connected = bridge._feedback_active = bridge._initial_complete = True
        bridge._received["system_on"] = True
        bridge.enqueue_command("MOTOR_1_ON", "test")
        connection_epoch = bridge._connection_epoch
        bridge._set_feedback_error("simulated subscription failure")
        self.assertEqual(bridge.health()["received"], {})
        self.assertFalse(bridge.health()["initial_complete"])
        self.assertEqual(bridge.timing_records()[0]["ack_status"], "queued")
        self.assertEqual(bridge._queue.get_nowait()["epoch"], connection_epoch)
        self.assertEqual(bridge.health()["connection_epoch"], connection_epoch)

    def test_repeated_feedback_failure_does_not_advance_epoch(self):
        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()
        bridge._feedback_active = True
        bridge._set_feedback_error("read failed")
        feedback_epoch = bridge.health()["feedback_epoch"]
        bridge._set_feedback_error("read failed again")
        self.assertEqual(bridge.health()["feedback_epoch"], feedback_epoch)

    def test_changing_endpoint_discards_old_queue(self):
        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()
        bridge.enabled = bridge._connected = True
        bridge.enqueue_command("START", "test")
        bridge.configure_connection("opc.tcp://new-server:4840")
        self.assertTrue(bridge._queue.empty())
        self.assertEqual(bridge.timing_records()[0]["ack_status"], "endpoint_changed")

    def test_initial_read_is_complete_before_feedback_becomes_available(self):
        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()
        nodes = {name: object() for name in RECEIVE_NODE_IDENTIFIERS}

        class FakeClient:
            async def read_attributes(self, requested):
                return [_data_value(False)] * len(requested)

        _run_without_io(bridge._read_feedback(FakeClient(), nodes))
        health = bridge.health()
        self.assertTrue(health["initial_complete"])
        self.assertTrue(health["feedback_active"])
        self.assertEqual(len(health["received"]), 25)
        baseline = health["feedback_sequence"]
        bridge._record_feedback("motor_1_on", True)
        self.assertEqual(bridge.health()["feedback_sequence"], baseline + 1)

    def test_command_written_without_feedback_can_observe_first_matching_read(self):
        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()
        bridge.enabled = bridge._connected = True
        bridge._pulse_seconds = 0
        bridge.enqueue_command("START", "test")
        record = bridge._queue.get_nowait()
        writes = []

        async def write(client, node_id, value):
            writes.append((node_id, value))

        bridge._write_node_value = write
        _run_without_io(bridge._send_command(None, record))
        self.assertEqual(writes, [(COMMAND_TO_NODE["START"], True), (COMMAND_TO_NODE["START"], False)])
        self.assertEqual(record["ack_status"], "pending")

        class FakeClient:
            async def read_attributes(self, requested):
                return [_data_value(True)]

        bridge._set_feedback_error("temporarily unavailable")
        bridge._record_feedback_locked("system_on", True, sample_started=record["started"] - 1)
        self.assertEqual(record["ack_status"], "pending")
        _run_without_io(bridge._read_feedback(FakeClient(), {"system_on": object()}))
        self.assertEqual(record["ack_status"], "state_observed")

    def test_bad_node_does_not_discard_other_nodes_or_keep_a_stale_value(self):
        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()

        class FakeClient:
            async def read_attributes(self, requested):
                return [_data_value(True), _data_value(False), _data_value(True, "BadNodeIdUnknown")]

        bridge._received["robot_metal"] = True
        nodes = {"system_on": "ns=5;i=2", "system_stopped": "ns=5;i=3", "robot_metal": "ns=5;i=24"}
        with self.assertLogs("blanky.opcua_service", level="WARNING"):
            self.assertFalse(_run_without_io(bridge._read_feedback(FakeClient(), nodes)))
        health = bridge.health()
        self.assertFalse(health["initial_complete"])
        self.assertTrue(health["feedback_active"])
        self.assertEqual(health["received"], {"system_on": True, "system_stopped": False})
        self.assertIn("ns=5;i=24", health["feedback_error"])
        self.assertIn("BadNodeIdUnknown", health["feedback_error"])

    def test_read_reduces_batch_size_on_server_operation_limit(self):
        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()
        nodes = dict(RECEIVE_NODE_IDENTIFIERS)
        sizes = []

        class FakeClient:
            async def read_attributes(self, requested):
                sizes.append(len(requested))
                if len(requested) > 2:
                    raise type("BadTooManyOperations", (Exception,), {"code": 123})()
                return [_data_value(False)] * len(requested)

        fake_ua = SimpleNamespace(StatusCodes=SimpleNamespace(BadTooManyOperations=123))
        with patch.object(opcua_service, "ua", fake_ua):
            self.assertTrue(_run_without_io(bridge._read_feedback(FakeClient(), nodes)))
            sizes.clear()
            self.assertTrue(_run_without_io(bridge._read_feedback(FakeClient(), nodes)))
        self.assertLessEqual(max(sizes), 2)
        self.assertEqual(bridge.health()["feedback_count"], len(nodes))

    def test_good_null_is_reported_without_inventing_a_plc_state(self):
        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()

        class FakeClient:
            async def read_attributes(self, requested):
                return [_data_value(self.value)] * len(requested)

        client = FakeClient()
        client.value = None
        nodes = dict(RECEIVE_NODE_IDENTIFIERS)
        with self.assertLogs("blanky.opcua_service", level="WARNING"):
            self.assertFalse(_run_without_io(bridge._read_feedback(client, nodes)))
        health = bridge.health()
        self.assertEqual(health["feedback_null_count"], 25)
        self.assertIn("Good/Null", health["feedback_error"])
        self.assertEqual(health["received"], {})
        self.assertFalse(health["feedback_active"])
        client.value = False
        self.assertTrue(_run_without_io(bridge._read_feedback(client, nodes)))
        self.assertTrue(bridge.health()["feedback_active"])
        self.assertEqual(bridge.health()["feedback_null_count"], 0)

    def test_subscription_partial_rejection_keeps_read_values_and_uses_polling(self):
        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()
        deleted = []

        class FakeSubscription:
            async def subscribe_data_change(self, nodes):
                return ["BadTooManyMonitoredItems"] + list(range(1, len(nodes)))

            async def delete(self):
                deleted.append(True)

        class FakeClient:
            async def get_namespace_index(self, uri):
                return 5

            def get_node(self, nodeid):
                return SimpleNamespace(nodeid=nodeid)

            async def read_attributes(self, requested):
                return [_data_value(False)] * len(requested)

            async def create_subscription(self, period, handler):
                return FakeSubscription()

        with self.assertLogs("blanky.opcua_service", level="WARNING"):
            subscription, nodes = _run_without_io(bridge._start_feedback(FakeClient()))
        self.assertIsNone(subscription)
        self.assertEqual(deleted, [True])
        self.assertEqual(bridge.health()["feedback_mode"], "polling")
        self.assertEqual(bridge.health()["feedback_count"], len(nodes))

    def test_pulse_resets_after_success_and_failed_true_write(self):
        variant = types.SimpleNamespace(Int16="i16", Int32="i32", Int64="i64", Float="f32", Double="f64", Boolean="bool")
        fake_ua = types.SimpleNamespace(VariantType=variant, Variant=lambda value, kind: value, DataValue=lambda value: value)

        class FakeNode:
            def __init__(self, fail=False):
                self.values = []
                self.fail = fail

            async def read_data_type_as_variant_type(self):
                return "bool"

            async def write_value(self, value):
                self.values.append(value)
                if self.fail and value:
                    raise OSError("simulated write failure")

        for fail in (False, True):
            with self.subTest(fail=fail), patch.object(opcua_service, "ua", fake_ua), patch.object(opcua_service, "OPCUA_ENABLED", False):
                bridge = opcua_service.OPCUABridge()
                bridge.enabled = True
                bridge._connected = True
                bridge._pulse_seconds = 0
                bridge.enqueue_command("MOTOR_1_ON", "test")
                record = bridge._queue.get_nowait()
                node = FakeNode(fail)
                client = types.SimpleNamespace(get_node=lambda node_id: node)
                if fail:
                    with self.assertRaises(OSError):
                        _run_without_io(bridge._send_command(client, record))
                    self.assertEqual(record["ack_status"], "write_error")
                else:
                    _run_without_io(bridge._send_command(client, record))
                    self.assertIsNotNone(record["write_ms"])
                self.assertEqual(node.values, [True, False])


class OPCUAConcurrentFeedbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_command_is_written_while_initial_feedback_is_blocked(self):
        class FakeClient:
            def __init__(self, **kwargs):
                pass

            async def connect(self):
                pass

            async def disconnect(self):
                pass

        with patch.object(opcua_service, "OPCUA_ENABLED", False):
            bridge = opcua_service.OPCUABridge()
        bridge.enabled = True
        bridge._pulse_seconds = 0
        writes = []

        async def slow_feedback(client):
            bridge.enqueue_command("START")
            await asyncio.Future()

        async def write(client, node_id, value):
            writes.append(value)
            if not value:
                bridge._stop.set()

        bridge._start_feedback = slow_feedback
        bridge._write_node_value = write
        with patch.object(opcua_service, "Client", FakeClient):
            await asyncio.wait_for(bridge._run(), timeout=2)
        self.assertEqual(writes, [True, False])


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
            self.assertEqual(bridge.timing_records()[0]["ack_status"], "state_observed")
        finally:
            await asyncio.to_thread(bridge.close)

    async def test_missing_return_node_does_not_block_start_confirmation(self):
        await self.received_nodes["robot_metal"].delete()
        await self.received_nodes["system_stopped"].write_value(True)
        with patch.object(opcua_service, "OPCUA_URL", self.url), patch.object(
            opcua_service, "OPCUA_PULSE_SECONDS", 0.1
        ):
            bridge = opcua_service.OPCUABridge()
        try:
            await self._wait_for(lambda: bridge.health()["feedback_active"])
            self.assertEqual(bridge.health()["feedback_count"], 24)
            self.assertIn("BadNodeIdUnknown", bridge.health()["feedback_error"])
            self.assertTrue(bridge.enqueue_command("START"))
            await self._wait_for(lambda: bridge.health()["last_write_ms"] is not None)
            await self.received_nodes["system_stopped"].write_value(False)
            await self.received_nodes["system_on"].write_value(True)
            await self._wait_for(lambda: bridge.timing_records()[0]["ack_status"] == "state_observed")
            self.assertTrue(bridge.health()["received"]["system_on"])
            self.assertFalse(bridge.health()["received"]["system_stopped"])
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
            with bridge._lock:
                record = {
                    "id": 1, "time": "", "command": "START", "source": "test",
                    "node": COMMAND_TO_NODE["START"], "library": "asyncua", "queue_ms": None,
                    "write_ms": None, "ack_ms": None, "ack_status": "queued",
                    "queued_at": time.monotonic() - 6, "endpoint": self.url,
                    "epoch": bridge._connection_epoch,
                }
                bridge._timings.append(record)
                bridge._queue.put_nowait(record)
            await self._wait_for(lambda: bridge.timing_records()[0]["ack_status"] != "queued")
            self.assertEqual(bridge.timing_records()[0]["ack_status"], "stale_or_endpoint_changed")
            self.assertFalse(await self.server.get_node("ns=4;i=2").read_value())
        finally:
            await asyncio.to_thread(bridge.close)


if __name__ == "__main__":
    unittest.main()
