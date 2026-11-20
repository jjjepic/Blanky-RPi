import threading
import time
import logging
from datetime import datetime

from PySide6.QtCore import QThread, Signal

from blanky.config import INPUT_WAV
from blanky.audio_service import audio_info, record_wav, play_beep
from blanky.speech_service import is_openai_configured, stt_transcribe
from blanky.command_parser import interpret_online_items, parse_offline_items
from blanky.mqtt_service import get_mqtt_bridge
from blanky.audio_messages import operational_speech
from blanky.operator_events import pending_message


_LOG = logging.getLogger(__name__)


class VoiceWorker(QThread):
    status = Signal(object)
    recognized = Signal(object)
    commandRecognized = Signal(object)
    diagnostic = Signal(object)
    spoken = Signal(object)
    detailReady = Signal(object)
    preferenceRequested = Signal(object)
    done = Signal()

    def __init__(self, lang: str, tts_speed: float = 1.0, parent=None, audio_coordinator=None,
                 session_id: int = 0):
        super().__init__(parent)
        self.lang = lang  # "pt" ou "en"
        self.tts_speed = float(tts_speed)
        self._audio = audio_coordinator
        self._session_id = session_id

    def _emit_status(self, text: str):
        self.status.emit({"session": self._session_id, "text": text})

    def _emit_recognized(self, text: str):
        self.recognized.emit({"session": self._session_id, "text": text})

    def _emit_command(self, command: str):
        self.commandRecognized.emit({"session": self._session_id, "command": command})

    def _response_for_result(self, bridge, command: str, accepted: bool, message: str | None) -> str:
        if message:
            return message
        if accepted:
            return pending_message(command, self.lang)
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
                self._emit_status(
                    "Modo Online indisponível" if self.lang == "pt" else "Online mode unavailable"
                )
                self._emit_recognized(
                    "Configure a chave OpenAI em Definições." if self.lang == "pt"
                    else "Configure the OpenAI key in Settings."
                )
                return

            started_at = time.perf_counter()
            self._emit_status("A ouvir..." if self.lang == "pt" else "Listening...")
            if self._audio and not self._audio.wait_for_quiet():
                raise RuntimeError("Audio output did not stop before capture")
            play_beep()
            try:
                record_wav(INPUT_WAV)
            finally:
                if self._audio:
                    self._audio.end_capture()
            t_record = time.perf_counter()
            diag = audio_info().get("last_record_diag", {})
            self._emit_status("A perceber..." if self.lang == "pt" else "Understanding...")
            text = stt_transcribe(INPUT_WAV, self.lang)
            t_transcribe = time.perf_counter()
            self._emit_recognized(text if text else "")

            mqtt_bridge = get_mqtt_bridge()
            transcribe_duration = t_transcribe - t_record
            other_language = "en" if self.lang == "pt" else "pt"
            if not text:
                command = "NO_AUDIO"
                self._emit_command(command)
                accepted, message = mqtt_bridge.process_command(command, self.lang, source="voice")
                response = self._response_for_result(mqtt_bridge, command, accepted, message)
                speech = response
                speech_map = {self.lang: speech, other_language: mqtt_bridge.last_event_message(other_language)}
                self._emit_diagnostic(
                    diag,
                    text,
                    command,
                    accepted,
                    started_at,
                    transcribe_duration,
                )
            else:
                self._emit_status("A interpretar..." if self.lang == "pt" else "Interpreting...")
                try:
                    items = interpret_online_items(text, self.lang)
                except Exception:
                    items = []
                if not items:
                    items = parse_offline_items(text, self.lang)

                if not items:
                    command = "UNKNOWN"
                    self._emit_command(command)
                    accepted, message = mqtt_bridge.process_command(command, self.lang, source="voice")
                    response = self._response_for_result(mqtt_bridge, command, accepted, message)
                    speech = response
                    speech_map = {self.lang: speech, other_language: mqtt_bridge.last_event_message(other_language)}
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
                    spoken_parts = {"pt": [], "en": []}
                    for index, item in enumerate(items):
                        command = item["name"]
                        if item["type"] == "setting" or command in {"QUERY_SETTING", "QUERY_CLARIFY"}:
                            request = {"item": item, "language": self.lang, "done": threading.Event(),
                                       "answers": None, "all_answers": None, "speed": self.tts_speed}
                            self.preferenceRequested.emit(request)
                            if request["done"].wait(timeout=10) and request["answers"]:
                                response_part = request["answers"]["detail"]
                                spoken_part = request["answers"]["speech"]
                                other_spoken = request["all_answers"][other_language]["speech"]
                                self.tts_speed = float(request["speed"])
                                accepted = command != "BLOCKED_SETTING"
                            else:
                                response_part = "Não percebi. Podes repetir?" if self.lang == "pt" else "I didn't understand. Can you repeat?"
                                spoken_part = response_part
                                other_spoken = "I didn't understand. Can you repeat?" if self.lang == "pt" else "Não percebi. Podes repetir?"
                                accepted = False
                            diagnostic_name = "Definição" if self.lang == "pt" else "Setting"
                        elif item["type"] == "query":
                            accepted = True
                            parts = mqtt_bridge.answer_status_query_parts(
                                command, item.get("target") or item.get("component", ""),
                                self.lang, "voice", item.get("value", "")
                            )
                            response_part, spoken_part = parts["detail"], parts["speech"]
                            other_spoken = parts["localized_speech"][other_language]
                            diagnostic_name = "Consulta" if self.lang == "pt" else "Query"
                        else:
                            self._emit_command(command)
                            accepted, mqtt_message = mqtt_bridge.process_command(
                                command, self.lang, source="voice"
                            )
                            response_part = self._response_for_result(
                                mqtt_bridge, command, accepted, mqtt_message
                            )
                            if accepted and mqtt_message is None:
                                spoken_part = other_spoken = ""
                            else:
                                spoken_part = operational_speech(command, accepted, response_part, self.lang)
                                other_detail = mqtt_bridge.last_event_message(other_language)
                                other_spoken = operational_speech(command, accepted, other_detail, other_language)
                            diagnostic_name = command
                        if response_part:
                            responses.append(response_part)
                            spoken_parts[self.lang].append(spoken_part)
                            spoken_parts[other_language].append(other_spoken)
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
                    speech_map = {lang: " ".join(filter(None, spoken_parts[lang])) for lang in ("pt", "en")}
                    speech = speech_map[self.lang]
            if response:
                self._emit_status("Resposta pronta." if self.lang == "pt" else "Answer ready.")
                self.spoken.emit({"session": self._session_id, "localized": speech_map})
                self.detailReady.emit({"session": self._session_id, "detail": response})

        except Exception as exc:
            _LOG.exception("Voice interaction failed")
            self._emit_status("Ocorreu um erro" if self.lang == "pt" else "An error occurred")
            self.diagnostic.emit({
                "time": datetime.now().strftime("%H:%M:%S"), "language": self.lang,
                "capture": 0.0, "stt": 0.0, "end": "error", "command": "AUDIO",
                "text": str(exc), "result": "ERROR", "duration": 0.0,
            })
        finally:
            if self._audio:
                self._audio.end_capture()
            self.done.emit()
