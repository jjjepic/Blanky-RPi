import threading
import time
from datetime import datetime

from PySide6.QtCore import QThread, Signal

from blanky.config import INPUT_WAV, TTS_WAV
from blanky.audio_service import audio_info, record_wav, play_wav
from blanky.speech_service import is_openai_configured, stt_transcribe, tts_speak_to_wav
from blanky.command_parser import interpret_online_items, parse_offline_items
from blanky.mqtt_service import get_mqtt_bridge


class VoiceWorker(QThread):
    status = Signal(str)
    recognized = Signal(str)
    commandRecognized = Signal(str)
    diagnostic = Signal(object)
    spoken = Signal(str)
    detailReady = Signal(str)
    preferenceRequested = Signal(object)
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
        item: dict | None = None,
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
                "interpretation": item or {"type": "command", "name": command},
                "confidence": float((item or {}).get("confidence", 1.0)),
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
                speech = response
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
                    items = interpret_online_items(text, self.lang)
                except Exception:
                    items = []
                if not items:
                    items = parse_offline_items(text, self.lang)

                if not items:
                    command = "UNKNOWN"
                    self.commandRecognized.emit(command)
                    accepted, message = mqtt_bridge.process_command(command, self.lang, source="voice")
                    response = self._response_for_result(mqtt_bridge, command, accepted, message)
                    speech = response
                    self._emit_diagnostic(
                        diag,
                        text,
                        command,
                        accepted,
                        started_at,
                        transcribe_duration,
                    )
                else:
                    responses = []
                    spoken_parts = []
                    for index, item in enumerate(items):
                        command = item["name"]
                        if item["type"] == "setting" or command in {"QUERY_SETTING", "QUERY_CLARIFY"}:
                            request = {"item": item, "language": self.lang, "done": threading.Event(),
                                       "answers": None, "speed": self.tts_speed}
                            self.preferenceRequested.emit(request)
                            if request["done"].wait(timeout=10) and request["answers"]:
                                response_part = request["answers"]["detail"]
                                spoken_part = request["answers"]["speech"]
                                self.tts_speed = float(request["speed"])
                                accepted = command != "BLOCKED_SETTING"
                            else:
                                response_part = "Não percebi. Podes repetir?" if self.lang == "pt" else "I didn't understand. Can you repeat?"
                                spoken_part = response_part
                                accepted = False
                            diagnostic_name = "Definição" if self.lang == "pt" else "Setting"
                        elif item["type"] == "query":
                            accepted = True
                            parts = mqtt_bridge.answer_status_query_parts(
                                command, item.get("target") or item.get("component", ""),
                                self.lang, "voice", item.get("value", "")
                            )
                            response_part, spoken_part = parts["detail"], parts["speech"]
                            diagnostic_name = "Consulta" if self.lang == "pt" else "Query"
                        else:
                            self.commandRecognized.emit(command)
                            accepted, mqtt_message = mqtt_bridge.process_command(
                                command, self.lang, source="voice"
                            )
                            response_part = self._response_for_result(
                                mqtt_bridge, command, accepted, mqtt_message
                            )
                            spoken_part = response_part
                            diagnostic_name = command
                        if response_part:
                            responses.append(response_part)
                            spoken_parts.append(spoken_part)
                        self._emit_diagnostic(
                            diag,
                            text,
                            diagnostic_name,
                            accepted,
                            started_at,
                            transcribe_duration,
                            item,
                        )
                        if index < len(items) - 1:
                            time.sleep(0.3)
                    response = " ".join(responses)
                    speech = " ".join(spoken_parts)
            if response:
                mqtt_bridge.remember_interaction_response(response, self.lang, speech)
                self.status.emit("Resposta pronta." if self.lang == "pt" else "Answer ready.")
                self.spoken.emit(speech)
                self.detailReady.emit(response)
                t = threading.Thread(target=self._speak_async, args=(speech,), daemon=True)
                t.start()

        except Exception:
            self.status.emit("Ocorreu um erro" if self.lang == "pt" else "An error occurred")
        finally:
            self.done.emit()
