import importlib
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from blanky import openai_activity


class OpenAiActivityTests(unittest.TestCase):
    def setUp(self):
        importlib.reload(openai_activity)

    def test_success_and_failure_are_reported_without_probe(self):
        self.assertEqual(openai_activity.activity_snapshot(), {"active": 0, "last": None})
        with openai_activity.measure_request("STT"):
            self.assertEqual(openai_activity.activity_snapshot()["active"], 1)
        self.assertEqual(openai_activity.activity_snapshot()["last"]["operation"], "STT")
        self.assertTrue(openai_activity.activity_snapshot()["last"]["ok"])
        with self.assertRaises(ValueError):
            with openai_activity.measure_request("TTS"):
                raise ValueError("private API detail")
        result = openai_activity.activity_snapshot()
        self.assertEqual(result["active"], 0)
        self.assertEqual(result["last"]["operation"], "TTS")
        self.assertFalse(result["last"]["ok"])
        self.assertNotIn("private API detail", str(result))

    def test_tts_uses_selected_speed_and_natural_pt_instructions(self):
        fake_openai = types.ModuleType("openai")
        fake_openai.OpenAI = object
        with patch.dict(sys.modules, {"openai": fake_openai}):
            sys.modules.pop("blanky.speech_service", None)
            speech_service = importlib.import_module("blanky.speech_service")

        calls = []
        fake_client = types.SimpleNamespace(
            audio=types.SimpleNamespace(
                speech=types.SimpleNamespace(
                    create=lambda **kwargs: (calls.append(kwargs), types.SimpleNamespace(read=lambda: b"wave"))[1]
                )
            )
        )
        with tempfile.TemporaryDirectory() as folder, patch.object(speech_service, "_get_client", return_value=fake_client):
            target = os.path.join(folder, "voice.wav")
            speech_service.tts_speak_to_wav("Sistema pronto.", target, speed=0.8, lang="pt")
            with open(target, "rb") as audio_file:
                self.assertEqual(audio_file.read(), b"wave")
        self.assertEqual(calls[0]["speed"], 0.8)
        self.assertIn("português europeu", calls[0]["instructions"])


if __name__ == "__main__":
    unittest.main()
