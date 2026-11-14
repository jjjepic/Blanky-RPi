import re
import threading
import unittest

from blanky.mqtt_service import MQTTBridge
from blanky.preference_intents import handle_preference


class FakeController:
    def __init__(self):
        self.ttsVoice = "nova"
        self.ttsSpeed = 1.0
        self.soundVolume = 0.5
        self.language = "pt"
        self.appearanceMode = "dark"
        self.colorVisionProfile = "universal"
        self.audioSelectedProfile = "simple"
        self.appearanceTextScale = 1.0
        self.hoverAnimationsEnabled = True
        self.displayScaleProfile = "auto"
        self.textBotMode = "online"
        self.calls = []

    def _set(self, name, attribute, value):
        self.calls.append(name)
        setattr(self, attribute, value)

    def setTtsVoice(self, value): self._set("setTtsVoice", "ttsVoice", value)
    def setTtsSpeed(self, value): self._set("setTtsSpeed", "ttsSpeed", value)
    def setSoundVolume(self, value): self._set("setSoundVolume", "soundVolume", max(0.0, min(1.0, value)))
    def setLanguage(self, value): self._set("setLanguage", "language", value)
    def setAppearanceMode(self, value): self._set("setAppearanceMode", "appearanceMode", value)
    def setColorVisionProfile(self, value): self._set("setColorVisionProfile", "colorVisionProfile", value)
    def setAudioInputPreset(self, value): self._set("setAudioInputPreset", "audioSelectedProfile", value)
    def setAppearanceTextScale(self, value): self._set("setAppearanceTextScale", "appearanceTextScale", value)
    def setHoverAnimationsEnabled(self, value): self._set("setHoverAnimationsEnabled", "hoverAnimationsEnabled", value)
    def setDisplayScaleProfile(self, value): self._set("setDisplayScaleProfile", "displayScaleProfile", value)
    def setTextBotMode(self, value): self._set("setTextBotMode", "textBotMode", value)


class PreferenceIntentTests(unittest.TestCase):
    def setUp(self):
        self.controller = FakeController()

    def _run(self, target, value, kind="setting", name=None):
        return handle_preference(self.controller, {
            "type": kind, "name": name or ("QUERY_SETTING" if kind == "query" else "SET_SETTING"),
            "target": target, "value": value,
        }, "pt")

    def test_setters_respect_ranges_and_do_not_call_communications(self):
        cases = [
            ("volume", "70", "70"), ("voice", "coral", "Coral"),
            ("speech_speed", "slow", "lenta"), ("appearance", "light", "claro"),
            ("color_profile", "deutan", "deutan"), ("audio_profile", "balanced", "equilibrado"),
            ("text_scale", "125", "125"), ("animations", "off", "desligadas"),
            ("display_scale", "full_hd", "Full HD"), ("textbot_mode", "offline", "Offline"),
            ("language", "en", "inglês"),
        ]
        for target, value, expected in cases:
            with self.subTest(target=target):
                answers = self._run(target, value)
                self.assertIn(expected, answers["pt"]["speech"])
                self.assertIn("sem comando enviado ao PLC", answers["pt"]["detail"])
                self.assertLessEqual(len(answers["pt"]["speech"].split()), 12)
                self.assertNotRegex(answers["pt"]["speech"], r"[A-Z]{2,}_[A-Z_]+")
        self.assertNotIn("saveCommunicationSettings", self.controller.calls)
        self.assertNotIn("setOpenAiApiKey", self.controller.calls)

    def test_relative_and_clamped_values(self):
        self._run("volume", "increase")
        self.assertEqual(self.controller.soundVolume, 0.6)
        answer = self._run("text_scale", "125")
        self.assertEqual(self.controller.appearanceTextScale, 1.25)
        answer = self._run("text_scale", "increase")
        self.assertEqual(self.controller.appearanceTextScale, 1.25)
        self.assertIn("limite permitido", answer["pt"]["speech"])
        answer = self._run("volume", "150")
        self.assertEqual(self.controller.soundVolume, 1.0)
        self.assertIn("limite permitido", answer["pt"]["speech"])
        self._run("voice", "next")
        self.assertNotEqual(self.controller.ttsVoice, "coral")

    def test_queries_and_blocked_settings_are_read_only(self):
        self._run("volume", "", kind="query")
        self.assertEqual(self.controller.calls, [])
        blocked = self._run("", "", name="BLOCKED_SETTING")
        self.assertIn("menu", blocked["pt"]["speech"])
        self.assertEqual(self.controller.calls, [])
        clarification = self._run("volume", "", kind="query", name="QUERY_CLARIFY")
        self.assertIn("ou alterá-lo", clarification["pt"]["speech"])
        with self.assertRaises(ValueError):
            self._run("mqtt", "on")

    def test_setting_event_never_enters_plc_write_path(self):
        writes = []
        bridge = object.__new__(MQTTBridge)
        bridge._lock = threading.Lock()
        bridge._events = []
        bridge._next_event_id = 1
        bridge._event_generation = 0
        bridge._publish = lambda *args, **kwargs: None
        bridge._opcua = type("PLC", (), {"enqueue_command": lambda _, *args: writes.append(args)})()
        bridge.record_preference_event("text", self._run("volume", "60"))
        self.assertEqual(writes, [])
        self.assertEqual(bridge._events[0]["kind"], "setting")
        self.assertEqual(bridge._events[0]["source"], "text")


if __name__ == "__main__":
    unittest.main()
