import threading
import time
from datetime import datetime

from PySide6.QtCore import QThread, Signal

from blanky.config import INPUT_WAV, TTS_WAV
from blanky.audio_service import audio_info, record_wav, play_wav
from blanky.speech_service import stt_transcribe, tts_speak_to_wav
from blanky.command_parser import parse_command
from blanky.mqtt_service import get_mqtt_bridge


class VoiceWorker(QThread):
    status = Signal(str)
    recognized = Signal(str)
    commandRecognized = Signal(str)
    diagnostic = Signal(object)
    spoken = Signal(str)
    done = Signal()

    def __init__(self, lang: str, tts_speed: float = 1.0, parent=None):
        super().__init__(parent)
        self.lang = lang  # "pt" ou "en"
        self.tts_speed = float(tts_speed)

    def _speak_async(self, response: str):
        try:
            tts_speak_to_wav(response, TTS_WAV, speed=self.tts_speed)
            play_wav(TTS_WAV)
        except Exception:
            self.status.emit("Ocorreu um erro" if self.lang == "pt" else "An error occurred")

    def run(self):
        try:
            started_at = time.perf_counter()
            self.status.emit("A ouvir..." if self.lang == "pt" else "Listening...")
            record_wav(INPUT_WAV)
            t_record = time.perf_counter()
            diag = audio_info().get("last_record_diag", {})
            self.status.emit("A perceber..." if self.lang == "pt" else "Understanding...")
            text = stt_transcribe(INPUT_WAV, self.lang)
            t_transcribe = time.perf_counter()
            self.recognized.emit(text if text else "")

            command, response = parse_command(text, self.lang)
            self.commandRecognized.emit(command)

            mqtt_bridge = get_mqtt_bridge()
            accepted, mqtt_message = mqtt_bridge.process_command(command, self.lang, source="voice")
            if mqtt_message:
                response = mqtt_message

            self.diagnostic.emit(
                {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "language": self.lang,
                    "capture": float(diag.get("total_duration_s") or 0.0),
                    "stt": t_transcribe - t_record,
                    "end": str(diag.get("end_reason") or "--"),
                    "command": command,
                    "text": text or ("(sem áudio detetado)" if self.lang == "pt" else "(no audio detected)"),
                    "result": "OK" if accepted else "REJECT",
                    "duration": time.perf_counter() - started_at,
                }
            )
            if response:
                self.spoken.emit(response)

            t = threading.Thread(target=self._speak_async, args=(response,), daemon=True)
            t.start()

        except Exception:
            self.status.emit("Ocorreu um erro" if self.lang == "pt" else "An error occurred")
        finally:
            self.done.emit()
