import types
import unittest

from blanky.mqtt_monitor import health_monitor_updates, state_monitor_updates
from blanky.mqtt_topics import COMMAND_TO_TOPIC

try:
    from blanky.mqtt_service import MQTTBridge
except ImportError:
    MQTTBridge = None


def _state(**changes):
    state = dict.fromkeys((
        "start", "mode_fast", "mode_ideal", "mode_manual", "mode_change",
        "motor_1", "motor_2", "motor_3", "cyl_a", "cyl_b", "cyl_c", "cyl_d",
        "light_green", "light_red", "robot_metal", "robot_nonmetal",
    ), 0)
    state.update(changes)
    return state


class MonitorPayloadTests(unittest.TestCase):
    def test_mode_has_one_stable_value_and_two_readable_values(self):
        cases = (
            ({}, "stopped", "Sistema parado"),
            ({"start": 1}, "choose_mode", "Escolhe um modo"),
            ({"start": 1, "mode_manual": 1}, "manual", "Modo manual"),
            ({"start": 1, "mode_change": 1}, "changing", "Escolhe o novo modo"),
        )
        for changes, code, label in cases:
            with self.subTest(code=code):
                state = _state(**changes)
                updates = state_monitor_updates(state, "start")
                self.assertEqual(updates["monitor/mode"], code)
                self.assertEqual(updates["monitor/pt/mode"], label)
                self.assertIn("monitor/en/mode", updates)

    def test_component_text_is_localized_and_separate_from_commands(self):
        state = _state(motor_1=1, cyl_c=1, light_green=1, robot_metal=1)
        expected = {
            "motor_1": "Ligado", "cyl_c": "Avanço solicitado", "light_green": "Acesa",
            "robot_metal": "Destino: peças metálicas",
        }
        for key, label in expected.items():
            with self.subTest(key=key):
                updates = state_monitor_updates(state, key)
                topic = "monitor/pt/robot" if key.startswith("robot_") else f"monitor/pt/{key}"
                self.assertEqual(updates[topic], label)
                self.assertTrue(all(name.startswith("monitor/") for name in updates))
                self.assertFalse(set(updates) & set(COMMAND_TO_TOPIC.values()))
        state["robot_metal"] = 0
        self.assertEqual(state_monitor_updates(state, "robot_metal")["monitor/pt/robot"], "Sem destino ativo")

    def test_opcua_connection_and_feedback_are_not_conflated(self):
        topics = health_monitor_updates({"opcua_connected": True, "opcua_feedback_active": False})
        self.assertEqual(topics["monitor/opcua"], "connected")
        self.assertEqual(topics["monitor/opcua_feedback"], "unavailable")
        self.assertEqual(topics["monitor/pt/opcua_ack_time"], "Sem confirmação")
        measured = health_monitor_updates({
            "opcua_connected": True, "opcua_feedback_active": True,
            "opcua_last_write_ms": 12.5, "opcua_last_ack_ms": 28.34,
        })
        self.assertEqual(measured["monitor/pt/opcua_write_time"], "12.50 ms")
        self.assertEqual(measured["monitor/en/opcua_ack_time"], "28.34 ms")


class FakeClient:
    def __init__(self):
        self.messages = []
        self.subscriptions = []
        self.will = None
        self.disconnected = False
        self.stopped = False

    def will_set(self, *args, **kwargs):
        self.will = (args, kwargs)

    def publish(self, topic, payload, **kwargs):
        self.messages.append((topic, payload, kwargs))
        return types.SimpleNamespace(wait_for_publish=lambda timeout: None)

    def subscribe(self, topic, **kwargs):
        self.subscriptions.append(topic)

    def disconnect(self):
        self.disconnected = True

    def loop_stop(self):
        self.stopped = True


@unittest.skipUnless(MQTTBridge is not None, "MQTT bridge dependencies are not installed")
class MonitorBridgeTests(unittest.TestCase):
    def _bridge(self):
        bridge = object.__new__(MQTTBridge)
        bridge.enabled = True
        bridge._connected = True
        bridge._topic_prefix = "blanky"
        bridge._broker_host = "localhost"
        bridge._broker_port = 1883
        bridge._client_id = "test"
        bridge._username = ""
        bridge._password = ""
        bridge._monitor_health_cache = {}
        bridge._events = []
        bridge._next_event_id = 1
        bridge._event_generation = 0
        bridge._last_mqtt_panel_rx = 0.0
        bridge._opcua = types.SimpleNamespace(health=lambda: {"connected": False}, enqueue_command=lambda *a, **k: None)
        bridge.state = _state()
        bridge.client = FakeClient()
        return bridge

    def test_legacy_state_still_publishes_and_adds_read_only_text(self):
        bridge = self._bridge()
        bridge.state["start"] = 1
        bridge._publish("state/start", 1)
        published = {topic: value for topic, value, _ in bridge.client.messages}
        self.assertEqual(published["blanky/state/start"], "1")
        self.assertEqual(published["blanky/monitor/pt/system"], "Iniciado")
        self.assertEqual(published["blanky/monitor/mode"], "choose_mode")
        self.assertTrue(all(options["retain"] for _, _, options in bridge.client.messages))

    def test_last_message_is_readable_and_localized(self):
        bridge = self._bridge()
        bridge._add_event("MOTOR_1_ON", "mqtt_panel", False, "Primeiro, inicie o sistema.", "before_start")
        published = {topic: value for topic, value, _ in bridge.client.messages}
        self.assertEqual(published["blanky/monitor/pt/last_message"], "Primeiro, inicie o sistema.")
        self.assertEqual(published["blanky/monitor/en/last_message"], "First, start the system.")

    def test_connect_publishes_presence_and_only_subscribes_commands(self):
        bridge = self._bridge()
        bridge._connected = False
        bridge._on_connect(bridge.client, None, None, 0)
        published = {topic: value for topic, value, _ in bridge.client.messages}
        self.assertEqual(published["blanky/monitor/availability"], "online")
        self.assertEqual(published["blanky/monitor/pt/last_message"], "Sem atividade.")
        self.assertEqual(published["blanky/monitor/opcua"], "disconnected")
        self.assertTrue(all(topic.startswith("blanky/mqtt_") for topic in bridge.client.subscriptions))

    def test_health_updates_only_when_changed(self):
        bridge = self._bridge()
        health = {"opcua_connected": False, "opcua_feedback_active": False}
        bridge.publish_monitor_health(health)
        count = len(bridge.client.messages)
        bridge.publish_monitor_health(health)
        self.assertEqual(len(bridge.client.messages), count)
        bridge.publish_monitor_health({"opcua_connected": True, "opcua_feedback_active": False})
        self.assertEqual(len(bridge.client.messages), count + 3)

    def test_will_and_graceful_exit(self):
        bridge = self._bridge()
        bridge._mqtt = types.SimpleNamespace(Client=lambda **kwargs: FakeClient())
        client = bridge._create_client()
        self.assertEqual(client.will, (("blanky/monitor/availability",), {"payload": "offline", "qos": 1, "retain": True}))
        bridge.close()
        self.assertIn(("blanky/monitor/availability", "offline", {"qos": 1, "retain": True}), bridge.client.messages)
        self.assertTrue(bridge.client.disconnected)
        self.assertTrue(bridge.client.stopped)


if __name__ == "__main__":
    unittest.main()
