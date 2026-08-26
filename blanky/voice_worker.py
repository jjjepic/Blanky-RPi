import threading
import time
from datetime import datetime

from PySide6.QtCore import QThread, Signal

from blanky.config import INPUT_WAV, TTS_WAV
from blanky.audio_service import audio_info, record_wav, play_wav
from blanky.speech_service import is_openai_configured, stt_transcribe, tts_speak_to_wav
from blanky.command_parser import interpret_online_commands
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
            tts_speak_to_wav(response, TTS_WAV, speed=self.tts_speed, lang=self.lang)
            play_wav(TTS_WAV)
        except Exception:
            # A execução já foi confirmada; uma falha de TTS não deve substituir esse estado.
            return

    def _response_for_result(self, bridge, command: str, accepted: bool, message: str | None) -> str:
        if message:
            return message
        if accepted:
            return bridge.response_for_command(command, self.lang)
        return ""

    def _emit_diagnostic(
        self,
        diag: dict,
        text: str,
        command: str,
        accepted: bool,
        started_at: float,
        transcribe_duration: float,
    ):
        self.diagnostic.emit(
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "language": self.lang,
                "capture": float(diag.get("total_duration_s") or 0.0),
                "stt": transcribe_duration,
                "end": str(diag.get("end_reason") or "--"),
                "command": command,
                "text": text or ("(sem áudio detetado)" if self.lang == "pt" else "(no audio detected)"),
                "result": "OK" if accepted else "REJECT",
                "duration": time.perf_counter() - started_at,
            }
        )

    def run(self):
        try:
            if not is_openai_configured():
                self.status.emit(
                    "Modo Online indisponível" if self.lang == "pt" else "Online mode unavailable"
                )
                self.recognized.emit(
                    "Configure a chave OpenAI em Definições." if self.lang == "pt"
                    else "Configure the OpenAI key in Settings."
                )
                return

            started_at = time.perf_counter()
            self.status.emit("A ouvir..." if self.lang == "pt" else "Listening...")
            record_wav(INPUT_WAV)
            t_record = time.perf_counter()
            diag = audio_info().get("last_record_diag", {})
            self.status.emit("A perceber..." if self.lang == "pt" else "Understanding...")
            text = stt_transcribe(INPUT_WAV, self.lang)
            t_transcribe = time.perf_counter()
            self.recognized.emit(text if text else "")

            mqtt_bridge = get_mqtt_bridge()
            transcribe_duration = t_transcribe - t_record
            if not text:
                command = "NO_AUDIO"
                self.commandRecognized.emit(command)
                accepted, message = mqtt_bridge.process_command(command, self.lang, source="voice")
                response = self._response_for_result(mqtt_bridge, command, accepted, message)
                self._emit_diagnostic(
                    diag,
                    text,
                    command,
                    accepted,
                    started_at,
                    transcribe_duration,
                )
            else:
                self.status.emit("A interpretar..." if self.lang == "pt" else "Interpreting...")
                try:
                    commands = interpret_online_commands(text, self.lang)
                except Exception:
                    commands = []

                if not commands:
                    command = "UNKNOWN"
                    self.commandRecognized.emit(command)
                    accepted, message = mqtt_bridge.process_command(command, self.lang, source="voice")
                    response = self._response_for_result(mqtt_bridge, command, accepted, message)
                    self._emit_diagnostic(
                        diag,
                        text,
                        command,
                        accepted,
                        started_at,
                        transcribe_duration,
                    )
                else:
                    response = ""
                    for index, command in enumerate(commands):
                        self.commandRecognized.emit(command)
                        accepted, mqtt_message = mqtt_bridge.process_command(
                            command,
                            self.lang,
                            source="voice",
                        )
                        response = self._response_for_result(
                            mqtt_bridge,
                            command,
                            accepted,
                            mqtt_message,
                        )
                        self._emit_diagnostic(
                            diag,
                            text,
                            command,
                            accepted,
                            started_at,
                            transcribe_duration,
                        )
                        if index < len(commands) - 1:
                            time.sleep(0.3)
            if response:
                self.spoken.emit(response)
                t = threading.Thread(target=self._speak_async, args=(response,), daemon=True)
                t.start()

        except Exception:
            self.status.emit("Ocorreu um erro" if self.lang == "pt" else "An error occurred")
        finally:
            self.done.emit()
