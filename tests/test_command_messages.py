import importlib
import re
import sys
import threading
import types
import unittest
from unittest.mock import patch

from blanky.command_messages import REJECTION_TEXT, no_change_message, rejection_for_event, rejection_message
from blanky.mqtt_topics import COMMAND_TO_TOPIC

try:
    from blanky.mqtt_service import MQTTBridge
except ImportError:
    MQTTBridge = None


def _load_offline_parser():
    try:
        from blanky.command_parser import parse_command
    except ModuleNotFoundError as exc:
        if exc.name != "openai":
            raise
        fake_openai = types.ModuleType("openai")
        fake_openai.OpenAI = object
        with patch.dict(sys.modules, {"openai": fake_openai}):
            parse_command = importlib.import_module("blanky.command_parser").parse_command
    return parse_command


class CommandMessageTests(unittest.TestCase):
    def test_every_rejection_is_short_localized_and_has_no_internal_identifier(self):
        reasons = {"before_start", "choose_mode", "manual_only", "change_mode_first", "choose_new_mode", "unknown", "no_audio"}
        self.assertEqual(set(REJECTION_TEXT["pt"]), reasons)
        self.assertEqual(set(REJECTION_TEXT["en"]), reasons)
        self.assertEqual(REJECTION_TEXT["pt"], {
            "before_start": "Primeiro, inicie o sistema.",
            "choose_mode": "Escolha primeiro um modo: rápido, ideal ou manual.",
            "manual_only": "Os componentes só se comandam no modo manual. Mude primeiro de modo.",
            "change_mode_first": 'Para trocar de modo, use primeiro "Mudar de modo".',
            "choose_new_mode": "Escolha o novo modo: rápido, ideal ou manual.",
            "unknown": "Não percebi o pedido. Pode repetir?",
            "no_audio": "Não ouvi nada. Tente outra vez.",
        })
        forbidden = re.compile(r"\b(?:START|STOP)\b|\b[A-Z]{2,}_[A-Z0-9_]+\b")
        for lang in ("pt", "en"):
            for reason in reasons | {"no_change"}:
                for command in COMMAND_TO_TOPIC:
                    with self.subTest(lang=lang, reason=reason, command=command):
                        message = rejection_message(reason, lang, command)
                        self.assertFalse(forbidden.search(message), message)
                        self.assertEqual(message, rejection_for_event({"reason": reason, "command": command}, lang))
            for command in COMMAND_TO_TOPIC:
                message = no_change_message(command, lang)
                self.assertNotIn("pedido não altera", message)
                self.assertNotIn("request does not change", message)

        self.assertEqual(no_change_message("CYL_A_EXTEND", "pt"), "O cilindro A já está avançado.")
        self.assertEqual(no_change_message("MOTOR_1_ON", "pt"), "O motor 1 já está ligado.")
        self.assertEqual(no_change_message("STOP", "pt"), "O sistema já está parado.")

    def test_offline_parser_avoids_conflicting_words(self):
        parse_command = _load_offline_parser()
        cases = {
            "avança o cilindro a": "CYL_A_EXTEND",
            "avançar o cilindro a": "CYL_A_EXTEND",
            "para": "STOP",
            "parar": "STOP",
            "para o sistema": "STOP",
            "iniciar": "START",
            "robô vai para metal": "ROBOT_TO_METAL",
        }
        for phrase, expected in cases.items():
            with self.subTest(phrase=phrase):
                self.assertEqual(parse_command(phrase, "pt")[0], expected)
        self.assertNotEqual(parse_command("quero passar para manual", "pt")[0], "STOP")
        self.assertNotEqual(parse_command("quero ir para o sistema", "pt")[0], "STOP")
        self.assertEqual(parse_command("", "pt")[1], rejection_message("no_audio", "pt"))
        self.assertEqual(parse_command("pedido impossível", "pt")[1], rejection_message("unknown", "pt"))


@unittest.skipUnless(MQTTBridge is not None, "OPC UA test dependencies are not installed")
class WorkflowMessageTests(unittest.TestCase):
    def _bridge(self):
        bridge = object.__new__(MQTTBridge)
        bridge._lock = threading.Lock()
        bridge._events = []
        bridge._next_event_id = 1
        bridge._event_generation = 0
        bridge.state = {key: 0 for key in (
            "start", "mode_fast", "mode_ideal", "mode_manual", "mode_change",
            "motor_1", "motor_2", "motor_3", "cyl_a", "cyl_b", "cyl_c", "cyl_d",
            "light_green", "light_red", "robot_metal", "robot_nonmetal",
        )}
        bridge._publish = lambda *args, **kwargs: None
        bridge._publish_rejected = lambda *args, **kwargs: None
        bridge._emit_for_command = lambda *args, **kwargs: None
        bridge._opcua = types.SimpleNamespace(enqueue_command=lambda *args, **kwargs: None)
        return bridge

    def test_workflow_reason_and_event_match_response(self):
        cases = (
            ({}, "MODE_FAST", "before_start"),
            ({"start": 1}, "MOTOR_1_ON", "choose_mode"),
            ({"start": 1, "mode_fast": 1}, "MOTOR_1_ON", "manual_only"),
            ({"start": 1, "mode_fast": 1}, "MODE_IDEAL", "change_mode_first"),
            ({"start": 1, "mode_change": 1}, "MOTOR_1_ON", "choose_new_mode"),
            ({"start": 1, "mode_manual": 1}, "MODE_FAST", "change_mode_first"),
            ({}, "STOP", "no_change"),
            ({"start": 1, "mode_manual": 1}, "MOTOR_1_OFF", "no_change"),
            ({}, "UNKNOWN", "unknown"),
            ({}, "NO_AUDIO", "no_audio"),
        )
        for lang in ("pt", "en"):
            for state, command, reason in cases:
                with self.subTest(lang=lang, command=command, reason=reason):
                    bridge = self._bridge()
                    bridge.state.update(state)
                    accepted, message = bridge.process_command(command, lang, source="test")
                    self.assertFalse(accepted)
                    self.assertEqual(bridge._events[-1]["reason"], reason)
                    self.assertEqual(bridge._events[-1]["detail"], message)
                    self.assertEqual(rejection_for_event(bridge._events[-1], lang), message)
                    other_lang = "en" if lang == "pt" else "pt"
                    self.assertEqual(rejection_for_event(bridge._events[-1], other_lang), rejection_message(reason, other_lang, command))

    def test_accepted_workflow_is_unchanged(self):
        bridge = self._bridge()
        for command in ("START", "MODE_MANUAL", "MOTOR_1_ON"):
            with self.subTest(command=command):
                accepted, message = bridge.process_command(command, "pt", source="test")
                self.assertTrue(accepted)
                self.assertIsNone(message)
                self.assertEqual(bridge._events[-1]["command"], command)
                self.assertEqual(bridge._events[-1]["reason"], "")
        self.assertEqual(bridge.state["motor_1"], 1)


if __name__ == "__main__":
    unittest.main()
