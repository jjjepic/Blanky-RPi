import threading
import time
import unittest

from blanky.audio_coordinator import AudioCoordinator
from blanky.audio_messages import command_group_key, operational_speech


def wait_for(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.states = []
        self.delivered = []
        self.played = []
        self.synthesized = []

        def synth(text, path, voice, speed, language):
            self.synthesized.append(text)
            with open(path, "wb") as handle:
                handle.write(text.encode())

        def play(path, cancel, started):
            if cancel.is_set():
                return False
            started()
            with open(path, "rb") as handle:
                self.played.append(handle.read().decode())
            return True

        self.synth = synth
        self.play = play
        self.manager = AudioCoordinator(synth, play, lambda *args: self.states.append(args),
                                        lambda *args: self.delivered.append(args),
                                        group_window=0.05, max_group_wait=0.12)

    def tearDown(self):
        self.manager.close()

    def submit(self, text, **kwargs):
        self.manager.submit(text, voice="nova", speed=1.0, language="pt", **kwargs)

    def test_synthesis_does_not_block_submission_or_capture_and_stale_result_is_discarded(self):
        entered = threading.Event()
        release = threading.Event()

        def slow_synth(text, path, voice, speed, language):
            entered.set()
            release.wait(2)
            with open(path, "wb") as handle:
                handle.write(text.encode())

        self.manager.close()
        self.manager = AudioCoordinator(slow_synth, self.play, lambda *args: self.states.append(args),
                                        lambda *args: self.delivered.append(args))
        started = time.monotonic()
        self.submit("resposta antiga")
        self.assertLess(time.monotonic() - started, 0.1)
        self.assertTrue(entered.wait(1))
        started = time.monotonic()
        self.manager.begin_capture()
        self.assertLess(time.monotonic() - started, 0.1)
        self.assertTrue(self.manager.wait_for_quiet(0.2))
        release.set()
        self.manager.end_capture()
        self.submit("resposta nova")
        self.assertTrue(wait_for(lambda: "resposta nova" in self.played))
        self.assertNotIn("resposta antiga", self.played)

    def test_active_playback_is_interrupted_before_capture(self):
        playing = threading.Event()
        stopped = threading.Event()

        def long_play(path, cancel, started):
            started()
            playing.set()
            cancel.wait(2)
            stopped.set()
            return False

        self.manager.close()
        self.manager = AudioCoordinator(self.synth, long_play, lambda *args: self.states.append(args),
                                        lambda *args: self.delivered.append(args))
        self.submit("antiga")
        self.assertTrue(playing.wait(1))
        self.manager.begin_capture()
        self.assertTrue(self.manager.wait_for_quiet(1))
        self.assertTrue(stopped.is_set())
        self.manager.end_capture()

    def test_same_priority_keeps_event_order_when_tts_finishes_out_of_order(self):
        entered = threading.Event()
        release = threading.Event()

        def out_of_order_synth(text, path, voice, speed, language):
            if text == "primeiro":
                entered.set()
                release.wait(1)
            with open(path, "wb") as handle:
                handle.write(text.encode())

        self.manager.close()
        self.manager = AudioCoordinator(out_of_order_synth, self.play,
                                        lambda *args: self.states.append(args),
                                        lambda *args: self.delivered.append(args))
        self.submit("primeiro")
        self.assertTrue(entered.wait(1))
        self.submit("segundo")
        time.sleep(0.08)
        self.assertEqual(self.played, [])
        release.set()
        self.assertTrue(wait_for(lambda: len(self.played) == 2))
        self.assertEqual(self.played, ["primeiro", "segundo"])

    def test_urgent_synthesis_starts_while_operational_synthesis_is_delayed(self):
        normal_entered = threading.Event()
        urgent_entered = threading.Event()
        release = threading.Event()

        def synth(text, path, voice, speed, language):
            if text == "operacional":
                normal_entered.set()
                release.wait(1)
            if text == "urgente":
                urgent_entered.set()
            with open(path, "wb") as handle:
                handle.write(text.encode())

        self.manager.close()
        self.manager = AudioCoordinator(synth, self.play, lambda *args: self.states.append(args),
                                        lambda *args: self.delivered.append(args))
        self.submit("operacional", priority="operational")
        self.assertTrue(normal_entered.wait(1))
        self.submit("urgente", priority="critical")
        self.assertTrue(urgent_entered.wait(0.3))
        self.assertTrue(wait_for(lambda: "urgente" in self.played))
        release.set()

    def test_late_older_tts_does_not_block_newer_reply_indefinitely(self):
        entered = threading.Event()
        release = threading.Event()

        def synth(text, path, voice, speed, language):
            if text == "antiga":
                entered.set()
                release.wait(1)
            with open(path, "wb") as handle:
                handle.write(text.encode())

        self.manager.close()
        self.manager = AudioCoordinator(synth, self.play, lambda *args: self.states.append(args),
                                        lambda *args: self.delivered.append(args))
        self.manager._order_wait = 0.12
        self.submit("antiga")
        self.assertTrue(entered.wait(1))
        self.submit("nova")
        self.assertTrue(wait_for(lambda: "nova" in self.played))
        release.set()
        time.sleep(0.05)
        self.assertNotIn("antiga", self.played)
        self.assertTrue(any(state == "stale" for state, _ in self.states))

    def test_operational_group_has_bounded_wait_and_does_not_mix_user_reply(self):
        for number in range(5):
            self.submit(f"Motor {number} ligado.", priority="operational", group=True)
            time.sleep(0.03)
        self.submit("Como está o sistema?", priority="requested")
        self.assertTrue(wait_for(lambda: len(self.played) >= 2))
        grouped = [text for text in self.played if "Motor" in text]
        self.assertTrue(grouped)
        self.assertTrue("pedidos aceites" in grouped[0] or "Motor 0 ligado; Motor 1 ligado" in grouped[0])
        self.assertIn("Como está o sistema?", self.played)
        self.assertNotIn("Como está o sistema?", grouped[0])

    def test_requested_reply_preempts_operational_playback(self):
        first_started = threading.Event()
        interrupted = threading.Event()

        def slow_operational(path, cancel, started):
            with open(path, "rb") as handle:
                text = handle.read().decode()
            started()
            self.played.append(text)
            if text == "operacional":
                first_started.set()
                if cancel.wait(1):
                    interrupted.set()
                    return False
            return True

        self.manager.close()
        self.manager = AudioCoordinator(self.synth, slow_operational,
                                        lambda *args: self.states.append(args),
                                        lambda *args: self.delivered.append(args))
        self.submit("operacional", priority="operational")
        self.assertTrue(first_started.wait(1))
        self.submit("pergunta", priority="requested")
        self.assertTrue(interrupted.wait(1))
        self.assertTrue(wait_for(lambda: "pergunta" in self.played))

    def test_critical_warning_waits_for_capture_without_disappearing(self):
        self.manager.begin_capture()
        self.submit("Aviso crítico", priority="critical")
        time.sleep(0.08)
        self.assertEqual(self.played, [])
        self.manager.end_capture()
        self.assertTrue(wait_for(lambda: "Aviso crítico" in self.played))

    def test_other_interface_cannot_release_capture_reservation(self):
        self.manager.begin_capture()
        self.submit("resposta de texto", priority="requested")
        self.manager.cancel_pending()
        self.submit("resposta nova", priority="requested")
        time.sleep(0.08)
        self.assertEqual(self.played, [])
        self.manager.end_capture()
        self.assertTrue(wait_for(lambda: "resposta nova" in self.played))
        self.assertNotIn("resposta de texto", self.played)

    def test_cache_reuses_identical_tts_without_reusing_output_file(self):
        self.submit("Igual")
        self.assertTrue(wait_for(lambda: len(self.played) == 1))
        self.submit("Igual")
        self.assertTrue(wait_for(lambda: len(self.played) == 2))
        self.assertEqual(self.synthesized, ["Igual"])

    def test_group_keeps_latest_action_for_same_control(self):
        self.submit("Pedido para ligar motor 1 aceite.", priority="operational", group=True,
                    group_key="motor_1")
        self.submit("Pedido para desligar motor 1 aceite.", priority="operational", group=True,
                    group_key="motor_1")
        self.submit("Pedido para ligar motor 2 aceite.", priority="operational", group=True,
                    group_key="motor_2")
        self.assertTrue(wait_for(lambda: len(self.played) == 1))
        self.assertNotIn("para ligar motor 1", self.played[0])
        self.assertIn("desligar motor 1", self.played[0])
        self.assertIn("ligar motor 2", self.played[0])

    def test_delivered_reply_keeps_localizations_for_repeat(self):
        self.submit("Sistema parado.", localized={"pt": "Sistema parado.", "en": "System stopped."})
        self.assertTrue(wait_for(lambda: bool(self.delivered)))
        delivered = self.delivered[0][0]
        self.assertEqual(delivered["localized"]["en"], "System stopped.")
        self.assertEqual(delivered["language"], "pt")

    def test_synthesis_and_playback_failures_do_not_stop_future_jobs(self):
        def flaky_synth(text, path, voice, speed, language):
            if text == "falha TTS":
                raise RuntimeError("network unavailable")
            self.synth(text, path, voice, speed, language)

        def flaky_play(path, cancel, started):
            with open(path, "rb") as handle:
                if handle.read() == b"falha audio":
                    raise OSError("device unavailable")
            return self.play(path, cancel, started)

        self.manager.close()
        self.manager = AudioCoordinator(flaky_synth, flaky_play, lambda *args: self.states.append(args),
                                        lambda *args: self.delivered.append(args))
        self.submit("falha TTS")
        self.assertTrue(wait_for(lambda: any(state == "error" for state, _ in self.states)))
        self.submit("falha audio")
        self.assertTrue(wait_for(lambda: sum(state == "error" for state, _ in self.states) >= 2))
        self.submit("recuperado")
        self.assertTrue(wait_for(lambda: "recuperado" in self.played))
        self.assertEqual([args[0]["text"] for args in self.delivered], ["recuperado"])

    def test_muted_output_is_not_reported_as_device_failure(self):
        self.manager.close()
        self.manager = AudioCoordinator(self.synth, lambda path, cancel, started: False,
                                        lambda *args: self.states.append(args),
                                        lambda *args: self.delivered.append(args))
        self.submit("silenciado")
        self.assertTrue(wait_for(lambda: any(state == "skipped" for state, _ in self.states)))
        self.assertFalse(any(state == "error" for state, _ in self.states))
        self.assertEqual(self.delivered, [])

    def test_spoken_confirmation_does_not_claim_physical_completion(self):
        for language in ("pt", "en"):
            spoken = operational_speech("MOTOR_1_ON", True, "Motor 1 ativado.", language)
            self.assertIn("aceite" if language == "pt" else "accepted", spoken)
            self.assertNotIn("ativado", spoken)
        self.assertEqual(command_group_key("MOTOR_1_ON"), command_group_key("MOTOR_1_OFF"))


if __name__ == "__main__":
    unittest.main()
