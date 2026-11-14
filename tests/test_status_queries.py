import re
import sys
import threading
import types
import unittest
from unittest.mock import patch

from blanky.command_parser import interpret_online_items, parse_command, parse_offline_items, validate_items
from blanky.mqtt_service import MQTTBridge
from blanky.intent_diagnostics import interpretation_snapshot


class QueryParserTests(unittest.TestCase):
    def test_portuguese_queries(self):
        examples = {
            "como está o sistema?": ("QUERY_SYSTEM", ""),
            "em que modo estou?": ("QUERY_MODE", ""),
            "o cilindro A está avançado?": ("QUERY_COMPONENT", "cyl_a"),
            "o motor um está ligado?": ("QUERY_COMPONENT", "motor_1"),
            "como estão as luzes?": ("QUERY_COMPONENT", "lights"),
            "o MQTT está ligado?": ("QUERY_MQTT", ""),
            "como estão as comunicações?": ("QUERY_CONNECTIONS", ""),
            "há algum erro?": ("QUERY_ERRORS", ""),
            "o que posso fazer agora?": ("QUERY_OPTIONS", ""),
            "repete": ("REPEAT", ""),
        }
        for phrase, expected in examples.items():
            with self.subTest(phrase=phrase):
                item = parse_offline_items(phrase, "pt")[0]
                self.assertEqual((item["name"], item.get("component", "")), expected)
                self.assertEqual(item["type"], "query")

    def test_english_queries(self):
        examples = {
            "how is the system?": "QUERY_SYSTEM",
            "what mode am I in?": "QUERY_MODE",
            "is cylinder A extended?": "QUERY_COMPONENT",
            "is motor one on?": "QUERY_COMPONENT",
            "how are the lights?": "QUERY_COMPONENT",
            "is MQTT connected?": "QUERY_MQTT",
            "how are the communications?": "QUERY_CONNECTIONS",
            "are there any errors?": "QUERY_ERRORS",
            "what can I do now?": "QUERY_OPTIONS",
            "repeat": "REPEAT",
        }
        for phrase, name in examples.items():
            with self.subTest(phrase=phrase):
                self.assertEqual(parse_offline_items(phrase, "en")[0]["name"], name)

    def test_mixed_order_and_multiple_questions(self):
        items = parse_offline_items("liga o motor 1 e diz-me se o MQTT está ligado", "pt")
        self.assertEqual([item["name"] for item in items], ["MOTOR_1_ON", "QUERY_MQTT"])
        items = parse_offline_items("diz-me o estado do OPC UA e da OpenAI", "pt")
        self.assertEqual([item["name"] for item in items], ["QUERY_OPCUA", "QUERY_OPENAI"])
        items = parse_offline_items("tell me about OpenAI and OPC UA", "en")
        self.assertEqual([item["name"] for item in items], ["QUERY_OPENAI", "QUERY_OPCUA"])

    def test_question_never_becomes_action(self):
        self.assertEqual(parse_command("o motor 1 está ligado?", "pt")[0], "UNKNOWN")
        self.assertEqual(parse_offline_items("o motor 1 está ligado?", "pt")[0]["name"], "QUERY_COMPONENT")
        self.assertEqual(parse_offline_items("está no modo manual?", "pt")[0]["name"], "QUERY_MODE")
        self.assertEqual(parse_offline_items("podes ligar o motor 1?", "pt")[0]["name"], "MOTOR_1_ON")
        self.assertEqual(parse_offline_items("can you start the system?", "en")[0]["name"], "START")
        self.assertEqual(parse_offline_items("avança o cilindro A", "pt")[0]["name"], "CYL_A_EXTEND")

    def test_model_output_must_use_known_intents_and_components(self):
        items = validate_items([
            {"type": "command", "name": "START"},
            {"type": "query", "name": "QUERY_COMPONENT", "component": "motor_1"},
            {"type": "query", "name": "QUERY_COMPONENT", "component": "all"},
            {"type": "command", "name": "QUERY_SYSTEM"},
            {"type": "query", "name": "STOP"},
        ])
        self.assertEqual([item["name"] for item in items], ["START", "QUERY_COMPONENT"])

    def test_group_preference_and_typo_phrases(self):
        examples = {
            "quais os motores ligados": ("QUERY_COMPONENT_GROUP", "motors", "on"),
            "ha motores ativos?": ("QUERY_COMPONENT_GROUP", "motors", "on"),
            "como estão os motores?": ("QUERY_COMPONENT_GROUP", "motors", ""),
            "que cilindros estao avancados": ("QUERY_COMPONENT_GROUP", "cylinders", "extended"),
            "o que é que está ligado": ("QUERY_ACTIVE", "", ""),
            "que voz estás a usar": ("QUERY_SETTING", "voice", ""),
            "qual é o volume": ("QUERY_SETTING", "volume", ""),
            "fala mais devagar": ("SET_SETTING", "speech_speed", "slow"),
            "aumenta o volume": ("SET_SETTING", "volume", "increase"),
            "põe o volume a 60": ("SET_SETTING", "volume", "60"),
            "muda a voz para a coral": ("SET_SETTING", "voice", "coral"),
            "muda para o tema claro": ("SET_SETTING", "appearance", "light"),
            "muda para alto contraste": ("SET_SETTING", "appearance", "high_contrast"),
            "tema monocromático": ("SET_SETTING", "appearance", "monochrome"),
            "letra maior": ("SET_SETTING", "text_scale", "increase"),
            "bolume": ("QUERY_CLARIFY", "volume", ""),
            "cilindro bê está avançado?": ("QUERY_COMPONENT", "cyl_b", ""),
        }
        for phrase, expected in examples.items():
            with self.subTest(phrase=phrase):
                item = parse_offline_items(phrase, "pt")[0]
                self.assertEqual((item["name"], item.get("target", ""), item.get("value", "")), expected)
        mixed = parse_offline_items("liga o motor 2 e diz-me que motores estão ligados", "pt")
        self.assertEqual([item["name"] for item in mixed], ["MOTOR_2_ON", "QUERY_COMPONENT_GROUP"])
        self.assertEqual(parse_offline_items("muda a chave OpenAI", "pt")[0]["name"], "BLOCKED_SETTING")
        last = interpretation_snapshot()[-1]
        self.assertEqual(last["text"], "muda a chave OpenAI")
        self.assertEqual(last["items"][0]["confidence"], 1.0)

    def test_english_group_and_preference_phrases(self):
        examples = {
            "which motors are on": "QUERY_COMPONENT_GROUP",
            "which cylinders are extended": "QUERY_COMPONENT_GROUP",
            "what is on": "QUERY_ACTIVE",
            "which voice are you using": "QUERY_SETTING",
            "what is the volume": "QUERY_SETTING",
            "speak more slowly": "SET_SETTING",
            "increase the volume": "SET_SETTING",
            "set the volume to 60": "SET_SETTING",
            "change the voice to coral": "SET_SETTING",
            "switch to light theme": "SET_SETTING",
            "larger text": "SET_SETTING",
        }
        for phrase, name in examples.items():
            with self.subTest(phrase=phrase):
                self.assertEqual(parse_offline_items(phrase, "en")[0]["name"], name)

    def test_online_uses_strict_schema_and_rejects_low_confidence(self):
        content = '{"items":[{"type":"query","name":"QUERY_COMPONENT_GROUP","target":"motors","value":"on","confidence":0.9}]}'
        captured = {}
        fake_response = types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))])
        def create(**kwargs):
            captured.update(kwargs)
            return fake_response
        fake_client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create)))
        with patch.dict(sys.modules, {"openai": types.SimpleNamespace(OpenAI=lambda: fake_client)}):
            items = interpret_online_items("quais os motores ligados", "pt")
        self.assertEqual(items[0]["target"], "motors")
        schema = captured["response_format"]
        self.assertEqual(schema["type"], "json_schema")
        self.assertTrue(schema["json_schema"]["strict"])
        self.assertEqual(validate_items([{"type": "setting", "name": "SET_SETTING", "target": "volume",
                                          "value": "80", "confidence": 0.2}]), [])

    def test_online_interpreter_keeps_mixed_order(self):
        content = ('{"items":[{"type":"command","name":"MOTOR_1_ON"},'
                   '{"type":"query","name":"QUERY_MQTT"},'
                   '{"type":"query","name":"QUERY_COMPONENT","component":"all"}]}')
        fake_response = types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))])
        fake_client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(
            create=lambda **kwargs: fake_response)))
        with patch.dict(sys.modules, {"openai": types.SimpleNamespace(OpenAI=lambda: fake_client)}):
            items = interpret_online_items("liga o motor 1 e diz-me se o MQTT está ligado", "pt")
        self.assertEqual([item["name"] for item in items], ["MOTOR_1_ON", "QUERY_MQTT"])

    def test_online_model_cannot_turn_clear_question_into_command(self):
        content = '{"items":[{"type":"command","name":"MOTOR_1_ON"}]}'
        fake_response = types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))])
        fake_client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(
            create=lambda **kwargs: fake_response)))
        with patch.dict(sys.modules, {"openai": types.SimpleNamespace(OpenAI=lambda: fake_client)}):
            items = interpret_online_items("o motor 1 está ligado?", "pt")
        self.assertEqual(items[0]["type"], "query")
        self.assertEqual(items[0]["name"], "QUERY_COMPONENT")

    def test_online_cannot_turn_blocked_setting_into_mode_command(self):
        fake_client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(
            create=lambda **kwargs: self.fail("Blocked setting should not reach the model"))))
        with patch.dict(sys.modules, {"openai": types.SimpleNamespace(OpenAI=lambda: fake_client)}):
            items = interpret_online_items("muda a chave OpenAI", "pt")
        self.assertEqual(items[0]["name"], "BLOCKED_SETTING")
        self.assertEqual(parse_command("muda a chave OpenAI", "pt")[0], "UNKNOWN")

    def test_transcribed_cylinder_letter_is_safe_for_commands(self):
        self.assertEqual(parse_command("avança o cilindro bê", "pt")[0], "CYL_B_EXTEND")
        self.assertEqual(parse_command("avança o cilindro sem letra", "pt")[0], "UNKNOWN")


class QueryBridgeTests(unittest.TestCase):
    def setUp(self):
        self.writes = []
        self.published = []
        self.bridge = object.__new__(MQTTBridge)
        self.bridge._lock = threading.Lock()
        self.bridge.state = dict.fromkeys((
            "start", "mode_fast", "mode_ideal", "mode_manual", "mode_change",
            "motor_1", "motor_2", "motor_3", "cyl_a", "cyl_b", "cyl_c", "cyl_d",
            "light_green", "light_red", "robot_metal", "robot_nonmetal",
        ), 0)
        self.bridge._events = []
        self.bridge._next_event_id = 1
        self.bridge._event_generation = 0
        self.bridge._last_interaction_response = {"pt": "", "en": ""}
        self.bridge._publish = lambda topic, value, **kwargs: self.published.append((topic, value))
        self.bridge._emit_for_command = lambda command, emit_pulse=None: None
        self.bridge.health = lambda: {
            "mqtt_base_connected": False, "opcua_connected": False,
            "opcua_feedback_active": False, "opcua_received": {},
        }
        self.bridge._opcua = type("PLC", (), {"enqueue_command": lambda _, *args, **kwargs: self.writes.append(args)})()

    def test_queries_are_read_only_even_when_stopped(self):
        cases = (
            ("QUERY_SYSTEM", ""), ("QUERY_MODE", ""), ("QUERY_COMPONENT", "motor_1"),
            ("QUERY_MQTT", ""), ("QUERY_OPCUA", ""), ("QUERY_OPENAI", ""),
            ("QUERY_CONNECTIONS", ""), ("QUERY_ERRORS", ""),
            ("QUERY_LAST_EVENT", ""), ("QUERY_OPTIONS", ""), ("REPEAT", ""),
        )
        answers = [self.bridge.answer_status_query(name, component, lang, "text")
                   for lang in ("pt", "en") for name, component in cases]
        self.assertEqual(self.writes, [])
        self.assertTrue(all(event["kind"] == "query" and event["source"] == "text" for event in self.bridge._events))
        self.assertTrue(all(event["accepted"] for event in self.bridge._events))
        self.assertTrue(all(not re.search(r"[A-Z]{2,}_[A-Z_]+", answer) for answer in answers))
        self.assertEqual(self.bridge.state["start"], 0)

    def test_group_query_has_short_speech_and_detailed_provenance(self):
        self.bridge.state["motor_2"] = 1
        parts = self.bridge.answer_status_query_parts("QUERY_COMPONENT_GROUP", "motors", "pt", "voice", "on")
        self.assertEqual(parts["speech"], "Só o motor 2 está ligado.")
        self.assertIn("Estado interno", parts["detail"])
        self.assertLessEqual(len(parts["speech"].split()), 12)
        self.assertEqual(self.writes, [])
        self.assertEqual(self.bridge._events[-1]["kind"], "query")
        self.assertEqual(self.bridge._events[-1]["source"], "voice")
        unfiltered = self.bridge.answer_status_query_parts("QUERY_COMPONENT_GROUP", "motors", "pt", "text")
        self.assertIn("motor 1 desligado", unfiltered["speech"].lower())
        self.assertIn("motor 2 ligado", unfiltered["speech"].lower())
        self.assertIn("motor 3 desligado", unfiltered["speech"].lower())
        self.assertLessEqual(len(unfiltered["speech"].split()), 12)
        self.bridge.state["cyl_a"] = 1
        active = self.bridge.answer_status_query_parts("QUERY_ACTIVE", "", "pt", "text")
        self.assertIn("cilindro A", active["speech"])
        self.assertLessEqual(len(active["speech"].split()), 12)

    def test_component_answer_does_not_claim_physical_position(self):
        self.bridge.state["cyl_c"] = 1
        answer = self.bridge.answer_status_query("QUERY_COMPONENT", "cyl_c", "pt", "voice")
        self.assertIn("avanço solicitado", answer)
        self.assertIn("não uma posição física confirmada", answer)
        self.assertEqual(self.writes, [])

    def test_options_follow_existing_workflow(self):
        self.assertIn("iniciar", self.bridge.answer_status_query("QUERY_OPTIONS", "", "pt", "text"))
        self.bridge.state["start"] = 1
        self.assertIn("modo rápido", self.bridge.answer_status_query("QUERY_OPTIONS", "", "pt", "text"))
        self.bridge.state["mode_manual"] = 1
        self.assertIn("motores", self.bridge.answer_status_query("QUERY_OPTIONS", "", "pt", "text"))
        self.bridge.state["mode_manual"] = 0
        self.bridge.state["mode_fast"] = 1
        self.assertIn("mudar de modo", self.bridge.answer_status_query("QUERY_OPTIONS", "", "pt", "text"))
        self.assertEqual(self.writes, [])

    def test_repeat_uses_last_spoken_answer(self):
        self.bridge.remember_interaction_response("O sistema está parado.", "pt")
        answer = self.bridge.answer_status_query("REPEAT", "", "pt", "voice")
        self.assertEqual(answer, "O sistema está parado.")

    def test_mixed_command_and_query_share_order_but_only_command_writes(self):
        accepted, message = self.bridge.process_command("START", "pt", source="text")
        self.assertTrue(accepted)
        self.assertIsNone(message)
        self.assertEqual(self.bridge.last_event_message("pt"), "Iniciado.")
        answer = self.bridge.answer_status_query("QUERY_MQTT", "", "pt", "text")
        self.assertIn("MQTT está desligado", answer)
        self.assertEqual(len(self.writes), 1)
        self.assertEqual([event.get("kind", "command") for event in self.bridge._events], ["command", "query"])

    def test_last_event_names_source_action_and_result_without_identifiers(self):
        self.bridge._events.append({
            "id": 1, "source": "mqtt_panel", "command": "MOTOR_1_ON",
            "accepted": False, "reason": "before_start", "detail": "Primeiro, inicie o sistema.",
        })
        answer = self.bridge.answer_status_query("QUERY_LAST_EVENT", "", "pt", "text")
        self.assertIn("telemóvel", answer)
        self.assertIn("ligar o motor 1", answer)
        self.assertIn("recusado", answer)
        self.assertNotIn("MOTOR_1_ON", answer)


if __name__ == "__main__":
    unittest.main()
