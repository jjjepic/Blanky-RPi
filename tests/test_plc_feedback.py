"""PLC return is authoritative even when an interface has queued a request."""

import threading
import types
import unittest
from unittest.mock import patch

from blanky.mqtt_service import MQTTBridge
from blanky.opcua_nodes import RECEIVE_NODE_IDENTIFIERS
from blanky.plc_state import STATE_KEYS, project_plc_state


def plc_values():
    values = {name: False for name in RECEIVE_NODE_IDENTIFIERS}
    values.update({
        "system_stopped": True,
        "motor_1_off": True, "motor_2_off": True, "motor_3_off": True,
        "cyl_a_retracted": True, "cyl_b_retracted": True,
        "green_off": True, "red_off": True,
    })
    return values


class FakeOPC:
    def __init__(self):
        self.received = plc_values()
        self.connected = True
        self.feedback_active = True
        self.epoch = 1
        self.records = []

    def health(self):
        return {
            "connected": self.connected, "feedback_active": self.feedback_active,
            "initial_complete": self.feedback_active and RECEIVE_NODE_IDENTIFIERS.keys() <= self.received.keys(),
            "feedback_epoch": self.epoch,
            "received": dict(self.received), "last_valid_read": "2026-11-16T12:00:00",
        }

    def timing_records(self):
        return [dict(record) for record in self.records]

    def enqueue_command(self, command, source="unknown"):
        if not self.connected:
            return False
        record_id = len(self.records) + 1
        self.records.append({
            "id": record_id, "command": command, "source": source,
            "write_ms": None, "ack_status": "queued",
        })
        return record_id

    def write(self, record_id=1):
        self.records[record_id - 1].update(write_ms=12.0, ack_status="pending")

    def observe(self, signal, value=True, record_id=1):
        self.received[signal] = value
        self.records[record_id - 1]["ack_status"] = "state_observed"


def make_bridge(opc):
    bridge = object.__new__(MQTTBridge)
    bridge._lock = threading.Lock()
    bridge._opcua = opc
    bridge._ui_lang = "pt"
    bridge.enabled = False
    bridge._connected = False
    bridge._last_mqtt_panel_rx = 0.0
    bridge._broker_host = "localhost"
    bridge._broker_port = 1883
    bridge._topic_prefix = "blanky"
    bridge._client_id = "test"
    bridge._events = []
    bridge._next_event_id = 1
    bridge._event_generation = 0
    bridge._last_interaction_response = {"pt": "", "en": ""}
    bridge._pending_commands = {}
    bridge._plc_available = False
    bridge._control_mode = "plc"
    bridge._test_pulses = {}
    bridge._plc_epoch = None
    bridge._plc_received = {}
    bridge._plc_error_latched = False
    bridge._last_valid_read = ""
    bridge._last_known = {}
    bridge.state = {key: None for key in STATE_KEYS}
    bridge.state_quality = {key: "unavailable" for key in STATE_KEYS}
    bridge._publish = lambda *args, **kwargs: None
    bridge._publish_rejected = lambda *args, **kwargs: None
    bridge._emit_for_command = lambda *args, **kwargs: None
    return bridge


class PLCProjectionTests(unittest.TestCase):
    def test_all_25_values_and_initial_quality(self):
        self.assertEqual(len(RECEIVE_NODE_IDENTIFIERS), 25)
        values, quality = project_plc_state(plc_values(), True)
        self.assertEqual(values["start"], 0)
        self.assertEqual(values["motor_1"], 0)
        self.assertEqual(values["cyl_a"], 0)
        self.assertIsNone(values["cyl_c"])
        self.assertEqual(quality["cyl_c"], "position_unknown")
        self.assertTrue(all(value is None for value in project_plc_state(plc_values(), False)[0].values()))

    def test_complementary_conflicts_and_between_sensors_are_unknown(self):
        values = plc_values()
        values["motor_1_on"] = True
        state, quality = project_plc_state(values, True)
        self.assertIsNone(state["motor_1"])
        self.assertEqual(quality["motor_1"], "inconsistent")
        values["motor_1_on"] = values["motor_1_off"] = False
        values["cyl_a_retracted"] = False
        state, quality = project_plc_state(values, True)
        self.assertIsNone(state["motor_1"])
        self.assertIsNone(state["cyl_a"])

    def test_missing_or_inconsistent_system_pair_is_not_confirmed(self):
        for raw, expected_quality in (
            ({"system_on": True}, "unavailable"),
            ({"system_on": True, "system_stopped": True}, "inconsistent"),
        ):
            with self.subTest(raw=raw):
                state, quality = project_plc_state(raw, True)
                self.assertIsNone(state["start"])
                self.assertEqual(quality["start"], expected_quality)

    def test_c_d_advanced_sensor_and_robot_pickup_request(self):
        values = plc_values()
        values["cyl_c_advance_signal"] = True
        values["robot_metal"] = True
        values["robot_nonmetal"] = True
        state, _ = project_plc_state(values, True)
        self.assertEqual(state["cyl_c"], 1)
        self.assertIsNone(state["cyl_d"])
        self.assertEqual(state["robot_metal"], 1)
        self.assertEqual(state["robot_nonmetal"], 1)


class PLCBridgeTests(unittest.TestCase):
    def setUp(self):
        self.opc = FakeOPC()
        self.bridge = make_bridge(self.opc)

    def start_manual(self):
        self.opc.received.update(system_on=True, system_stopped=False, mode_manual=True)
        self.bridge.get_snapshot()

    def test_initial_snapshot_is_not_fake_event(self):
        snapshot = self.bridge.get_snapshot()
        self.assertEqual(snapshot["state"]["start"], 0)
        self.assertEqual(snapshot["events"], [])
        self.assertEqual(snapshot["last_valid_read"], "2026-11-16T12:00:00")

    def test_hmi_and_automatic_changes_need_no_blanky_command(self):
        self.bridge.get_snapshot()
        self.opc.received.update(system_on=True, system_stopped=False, mode_manual=True,
                                 motor_2_on=True, motor_2_off=False)
        snapshot = self.bridge.get_snapshot()
        self.assertEqual(snapshot["state"]["mode_manual"], 1)
        self.assertEqual(snapshot["state"]["motor_2"], 1)
        self.assertEqual(self.opc.records, [])
        self.assertTrue(any(event["reason"] == "state_change" for event in snapshot["events"]))

    def test_command_has_queued_written_observed_stages(self):
        self.bridge.get_snapshot()
        self.assertEqual(self.bridge.process_command("START", "pt", source="voice"), (True, None))
        self.assertEqual(self.bridge.get_snapshot()["state"]["start"], 0)
        self.opc.write()
        self.assertEqual(self.bridge.get_snapshot()["pending"]["start"]["stage"], "written")
        self.opc.received["system_stopped"] = False
        self.opc.observe("system_on")
        snapshot = self.bridge.get_snapshot()
        self.assertEqual(snapshot["state"]["start"], 1)
        self.assertNotIn("start", snapshot["pending"])
        self.assertEqual([e["reason"] for e in snapshot["events"] if e["command"] == "START"],
                         ["queued", "written", "state_observed"])

    def test_start_sends_without_initial_feedback_and_later_confirms(self):
        self.opc.feedback_active = False
        self.assertIsNone(self.bridge.get_snapshot()["state"]["start"])
        self.assertEqual(self.bridge.process_command("START", "pt", source="button"), (True, None))
        self.assertEqual(self.opc.records[0]["command"], "START")
        self.opc.write()
        self.assertIsNone(self.bridge.get_snapshot()["state"]["start"])
        self.opc.feedback_active = True
        self.opc.received["system_stopped"] = False
        self.opc.observe("system_on")
        snapshot = self.bridge.get_snapshot()
        self.assertEqual(snapshot["state"]["start"], 1)
        self.assertEqual(snapshot["state_quality"]["start"], "confirmed")
        self.assertNotIn("start", snapshot["pending"])
        self.assertEqual(snapshot["events"][-1]["reason"], "state_observed")

    def test_start_confirms_from_partial_return_and_hmi_can_stop(self):
        self.opc.received = {"system_on": False, "system_stopped": True}
        self.assertTrue(self.bridge.process_command("START", "pt", source="button")[0])
        self.opc.write()
        self.opc.received["system_stopped"] = False
        self.opc.observe("system_on")
        snapshot = self.bridge.get_snapshot()
        self.assertEqual(snapshot["state"]["start"], 1)
        self.assertIsNone(snapshot["state"]["motor_1"])
        self.assertNotIn("start", snapshot["pending"])
        self.assertEqual(snapshot["events"][-1]["reason"], "state_observed")
        self.opc.received.update(system_on=False, system_stopped=True)
        self.assertEqual(self.bridge.get_snapshot()["state"]["start"], 0)
        self.assertEqual(len(self.opc.records), 1)

    def test_missing_alarm_return_does_not_clear_a_known_alarm(self):
        self.opc.received["system_error"] = True
        self.bridge.get_snapshot()
        del self.opc.received["system_error"]
        self.assertFalse(self.bridge.process_command("START", "pt")[0])
        self.assertEqual(self.bridge.get_snapshot()["events"][-1]["reason"], "system_error")

    def test_pending_start_and_mode_allow_sequence_without_claiming_state(self):
        self.opc.feedback_active = False
        self.assertFalse(self.bridge.process_command("MODE_MANUAL", "pt")[0])
        for command, source in (("START", "mqtt_panel"), ("MODE_MANUAL", "text"), ("MOTOR_1_ON", "voice")):
            self.assertTrue(self.bridge.process_command(command, "pt", source=source)[0])
        snapshot = self.bridge.get_snapshot()
        self.assertEqual(snapshot["workflow"]["mode_manual"], 1)
        self.assertTrue(all(snapshot["state"][key] is None for key in ("start", "mode_manual", "motor_1")))
        self.assertTrue(self.bridge.process_command("STOP", "pt", source="button")[0])
        self.assertFalse(self.bridge.process_command("MOTOR_2_ON", "pt")[0])

    def test_start_with_inconsistent_bits_and_hmi_return(self):
        self.opc.received["system_stopped"] = False
        self.assertIsNone(self.bridge.get_snapshot()["state"]["start"])
        self.opc.received.update(system_on=True, mode_manual=True)
        snapshot = self.bridge.get_snapshot()
        self.assertEqual(snapshot["state"]["start"], 1)
        self.assertEqual(snapshot["workflow"]["mode_manual"], 1)
        self.assertTrue(any(event["plc_key"] == "start" for event in snapshot["events"]))
        self.assertEqual(self.opc.records, [])

    def test_unconfirmed_start_expires_and_disconnected_start_is_rejected(self):
        self.opc.feedback_active = False
        self.assertTrue(self.bridge.process_command("START", "pt")[0])
        self.opc.records[0]["ack_status"] = "timeout"
        self.assertIsNone(self.bridge.get_snapshot()["workflow"]["start"])
        self.opc.connected = False
        self.assertFalse(self.bridge.process_command("START", "pt")[0])
        self.assertEqual(self.bridge.get_snapshot()["events"][-1]["reason"], "opcua_unavailable")

    def test_mqtt_state_is_published_only_after_confirmed_return(self):
        published = []
        self.bridge._publish = lambda topic, value, **kwargs: published.append((topic, value))
        self.start_manual()
        published.clear()
        self.assertTrue(self.bridge.process_command("MOTOR_1_ON", "pt")[0])
        self.assertNotIn(("state/motor_1", 1), published)
        self.opc.write()
        self.opc.received["motor_1_off"] = False
        self.opc.observe("motor_1_on")
        self.bridge.get_snapshot()
        self.assertIn(("state/motor_1", 1), published)
        self.assertIn(("state_quality/motor_1", "confirmed"), published)

    def test_motor_started_on_hmi_can_be_commanded_off_by_blanky(self):
        self.start_manual()
        for index, source in ((1, "button"), (2, "text")):
            with self.subTest(motor=index, source=source):
                key = f"motor_{index}"
                self.opc.received.update({f"{key}_on": True, f"{key}_off": False})
                self.assertEqual(self.bridge.get_snapshot()["state"][key], 1)
                command = f"MOTOR_{index}_OFF"
                self.assertEqual(self.bridge.process_command(command, "pt", source=source), (True, None))
                self.assertEqual(self.opc.records[-1]["command"], command)
                self.opc.write(record_id=index)
                self.assertEqual(self.bridge.get_snapshot()["state"][key], 1)
                self.opc.received[f"{key}_on"] = False
                self.opc.observe(f"{key}_off", record_id=index)
                snapshot = self.bridge.get_snapshot()
                self.assertEqual(snapshot["state"][key], 0)
                self.assertEqual(snapshot["state_quality"][key], "confirmed")
                self.assertEqual(snapshot["events"][-1]["reason"], "state_observed")

    def test_pending_duplicate_and_timeout_do_not_fake_state(self):
        self.start_manual()
        self.assertTrue(self.bridge.process_command("MOTOR_1_ON", "pt")[0])
        self.assertFalse(self.bridge.process_command("MOTOR_1_ON", "pt")[0])
        self.assertEqual(self.bridge.state["motor_1"], 0)
        self.opc.records[0]["ack_status"] = "timeout"
        snapshot = self.bridge.get_snapshot()
        self.assertEqual(snapshot["state"]["motor_1"], 0)
        self.assertNotIn("motor_1", snapshot["pending"])
        self.assertEqual(snapshot["events"][-1]["reason"], "timeout")

    def test_failed_write_and_already_matching_state(self):
        self.start_manual()
        self.assertFalse(self.bridge.process_command("MOTOR_1_OFF", "pt")[0])
        self.assertTrue(self.bridge.process_command("MOTOR_1_ON", "pt")[0])
        self.opc.records[0]["ack_status"] = "write_error"
        self.bridge.get_snapshot()
        self.assertEqual(self.bridge.state["motor_1"], 0)
        self.assertEqual(self.bridge._events[-1]["reason"], "write_error")

    def test_stop_can_override_pending_start(self):
        self.bridge.get_snapshot()
        self.assertTrue(self.bridge.process_command("START", "pt")[0])
        self.assertTrue(self.bridge.process_command("STOP", "pt")[0])
        self.assertEqual(self.bridge.state["start"], 0)
        self.assertEqual(self.bridge._pending_commands["start"]["command"], "STOP")
        self.assertTrue(any(event["reason"] == "superseded_by_stop" for event in self.bridge._events))

    def test_retained_phone_command_cannot_trigger_write(self):
        self.start_manual()
        message = types.SimpleNamespace(topic="blanky/mqtt_motor_1", payload=b"1", retain=True)
        self.bridge._on_message(None, None, message)
        self.assertEqual(self.opc.records, [])

    def test_disconnect_invalidates_and_reconnect_rebaselines(self):
        self.start_manual()
        self.opc.connected = self.opc.feedback_active = False
        snapshot = self.bridge.get_snapshot()
        self.assertIsNone(snapshot["state"]["start"])
        self.assertEqual(snapshot["state_quality"]["motor_1"], "unavailable")
        count = len(snapshot["events"])
        self.opc.connected = self.opc.feedback_active = True
        self.opc.epoch += 1
        self.opc.received["motor_1_on"] = True
        self.opc.received["motor_1_off"] = False
        snapshot = self.bridge.get_snapshot()
        self.assertEqual(snapshot["state"]["motor_1"], 1)
        self.assertEqual(len(snapshot["events"]), count)

    def test_c_d_retraction_is_rejected_from_every_route(self):
        self.start_manual()
        for source in ("voice", "text", "button", "mqtt_panel", "mqtt_text"):
            for command in ("CYL_C_RETRACT", "CYL_D_RETRACT"):
                accepted, message = self.bridge.process_command(command, "pt", source=source)
                self.assertFalse(accepted)
                self.assertIn("HMI", message)
        self.assertEqual(self.opc.records, [])
        self.assertTrue(self.bridge.process_command("CYL_C_EXTEND", "pt")[0])

    def test_distinct_pickup_requests_can_be_queued_sequentially(self):
        self.start_manual()
        self.assertTrue(self.bridge.process_command("ROBOT_TO_METAL", "pt")[0])
        self.assertTrue(self.bridge.process_command("ROBOT_TO_NONMETAL", "pt")[0])
        self.assertEqual(len(self.opc.records), 2)
        self.assertEqual(self.bridge.state["robot_metal"], 0)
        self.assertEqual(self.bridge.state["robot_nonmetal"], 0)

    def test_queries_use_feedback_and_never_write(self):
        self.start_manual()
        self.assertIn("desligada", self.bridge.answer_status_query("QUERY_COMPONENT", "light_green", "pt", "voice"))
        self.assertIn("não tem avanço confirmado", self.bridge.answer_status_query("QUERY_COMPONENT", "cyl_c", "pt", "voice"))
        self.assertIn("Não há pedido", self.bridge.answer_status_query("QUERY_COMPONENT", "robot", "pt", "voice"))
        self.assertEqual(self.opc.records, [])

    def test_reset_session_does_not_reset_plc_state(self):
        self.start_manual()
        self.bridge.reset_system("pt")
        self.assertEqual(self.bridge.state["start"], 1)
        self.assertEqual(self.bridge.state["mode_manual"], 1)


class LocalTestModeTests(unittest.TestCase):
    def setUp(self):
        self.opc = FakeOPC()
        self.bridge = make_bridge(self.opc)

    def test_without_plc_updates_locally_and_does_not_claim_delivery(self):
        self.opc.connected = self.opc.feedback_active = False
        self.assertTrue(self.bridge.set_control_mode("test"))
        for command, source in (("START", "voice"), ("MODE_MANUAL", "text"),
                                ("MOTOR_1_ON", "button")):
            self.assertTrue(self.bridge.process_command(command, "pt", source=source)[0])
        snapshot = self.bridge.get_snapshot()
        self.assertEqual(snapshot["control_mode"], "test")
        self.assertEqual(snapshot["state"]["motor_1"], 1)
        self.assertEqual(snapshot["state_quality"]["motor_1"], "local")
        self.assertEqual(self.opc.records, [])
        self.assertIn("não chegou", snapshot["events"][-1]["detail"])
        self.assertIn("local", self.bridge.answer_status_query("QUERY_COMPONENT", "motor_1", "pt", "voice"))

    def test_connected_test_still_sends_but_ignores_feedback_until_return(self):
        self.assertTrue(self.bridge.set_control_mode("test"))
        self.assertTrue(self.bridge.process_command("START", "pt", source="mqtt_panel")[0])
        self.assertEqual(self.opc.records[0]["command"], "START")
        self.assertEqual(self.bridge.get_snapshot()["state"]["start"], 1)
        self.assertEqual(self.bridge.get_snapshot()["pending"], {})
        self.assertFalse(any(event["reason"] == "state_observed" for event in self.bridge._events))
        self.assertTrue(self.bridge.set_control_mode("plc"))
        self.assertEqual(self.bridge.get_snapshot()["state"]["start"], 0)
        self.assertEqual(self.bridge.get_snapshot()["state_quality"]["start"], "confirmed")
        self.opc.received.update(system_on=True, system_stopped=False)
        self.assertEqual(self.bridge.get_snapshot()["state"]["start"], 1)

    def test_pending_request_prevents_mode_change(self):
        self.bridge.get_snapshot()
        self.assertTrue(self.bridge.process_command("START", "pt")[0])
        self.assertFalse(self.bridge.set_control_mode("test"))
        self.assertEqual(self.bridge.control_mode, "plc")

    def test_test_mode_preserves_validation_and_stop(self):
        self.assertTrue(self.bridge.set_control_mode("test"))
        self.assertFalse(self.bridge.process_command("MOTOR_1_ON", "pt")[0])
        self.assertTrue(self.bridge.process_command("START", "pt")[0])
        self.assertFalse(self.bridge.process_command("MOTOR_1_ON", "pt")[0])
        self.assertTrue(self.bridge.process_command("MODE_MANUAL", "pt")[0])
        self.assertFalse(self.bridge.process_command("CYL_C_RETRACT", "pt")[0])
        self.assertTrue(self.bridge.process_command("MOTOR_1_ON", "pt")[0])
        self.assertTrue(self.bridge.process_command("STOP", "pt")[0])
        self.assertEqual(self.bridge.get_snapshot()["state"]["motor_1"], 0)

    def test_known_plc_error_still_blocks_test_commands(self):
        self.opc.received["system_error"] = True
        self.assertTrue(self.bridge.set_control_mode("test"))
        self.assertEqual(self.bridge.get_snapshot()["state"]["system_error"], 1)
        self.assertEqual(self.bridge.get_snapshot()["state_quality"]["system_error"], "confirmed")
        self.assertTrue(any(event["reason"] == "system_error" for event in self.bridge._events))
        self.assertFalse(self.bridge.process_command("START", "pt")[0])
        self.assertEqual(self.opc.records, [])
        self.opc.connected = self.opc.feedback_active = False
        self.assertEqual(self.bridge.get_snapshot()["state"]["system_error"], 1)
        self.assertFalse(self.bridge.process_command("START", "pt")[0])

    def test_c_d_and_robot_test_pulses_reset_after_two_seconds(self):
        timers = []

        class FakeTimer:
            def __init__(self, delay, callback):
                self.delay = delay
                self.callback = callback
                self.cancelled = False
                timers.append(self)

            def start(self):
                pass

            def cancel(self):
                self.cancelled = True

            def fire(self):
                if not self.cancelled:
                    self.callback()

        published = []
        self.bridge._publish = lambda topic, value, **kwargs: published.append((topic, value))
        self.assertTrue(self.bridge.set_control_mode("test"))
        with patch("blanky.mqtt_service.threading.Timer", FakeTimer):
            self.assertTrue(self.bridge.process_command("START", "pt")[0])
            self.assertTrue(self.bridge.process_command("MODE_MANUAL", "pt")[0])
            for command, key, topic in (
                ("CYL_C_EXTEND", "cyl_c", "mqtt_cyl_c"),
                ("CYL_D_EXTEND", "cyl_d", "mqtt_cyl_d"),
                ("ROBOT_TO_METAL", "robot_metal", "mqtt_robot_to_metal"),
            ):
                self.assertTrue(self.bridge.process_command(command, "pt")[0])
                timer = timers[-1]
                self.assertEqual(timer.delay, 2.0)
                self.assertEqual(self.bridge.state[key], 1)
                self.assertIn((topic, "1"), published)
                timer.fire()
                self.assertEqual(self.bridge.state[key], 0)
                self.assertIn((topic, "0"), published)
            self.assertTrue(self.bridge.process_command("ROBOT_TO_NONMETAL", "pt")[0])
            self.assertTrue(self.bridge.process_command("CYL_C_EXTEND", "pt")[0])
            pending_timer = timers[-1]
            self.assertTrue(self.bridge.process_command("STOP", "pt")[0])
            self.assertTrue(pending_timer.cancelled)
            self.assertEqual(self.bridge.state["cyl_c"], 0)

    def test_switch_to_plc_cancels_local_pulse_without_stale_reset(self):
        class FakeTimer:
            def __init__(self, delay, callback):
                self.callback = callback
                self.cancelled = False

            def start(self):
                pass

            def cancel(self):
                self.cancelled = True

        self.assertTrue(self.bridge.set_control_mode("test"))
        with patch("blanky.mqtt_service.threading.Timer", FakeTimer):
            self.assertTrue(self.bridge.process_command("START", "pt")[0])
            self.assertTrue(self.bridge.process_command("MODE_MANUAL", "pt")[0])
            self.assertTrue(self.bridge.process_command("CYL_D_EXTEND", "pt")[0])
            timer = self.bridge._test_pulses["cyl_d"][0]
            self.assertTrue(self.bridge.set_control_mode("plc"))
            self.assertTrue(timer.cancelled)
            self.assertIsNone(self.bridge.get_snapshot()["state"]["cyl_d"])
            timer.callback()
            self.assertIsNone(self.bridge.get_snapshot()["state"]["cyl_d"])


if __name__ == "__main__":
    unittest.main()
