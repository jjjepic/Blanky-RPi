import os
import csv
import queue
import threading
import html
import textwrap
import re
from datetime import datetime

from PySide6.QtCore import QCoreApplication, QObject, Property, QTimer, QUrl, Signal, Slot

from blanky.audio_service import (
    apply_audio_input_preset,
    audio_info,
    get_audio_input_preset,
    get_audio_input_settings,
    get_audio_output_volume,
    is_audio_output_enabled,
    play_beep,
    play_wav,
    set_audio_output_enabled,
    set_audio_output_volume,
    stop_playback,
    update_audio_input_settings,
)
from blanky.config import AUDIO_DIR, WAKEWORD_ENABLED
from blanky.mqtt_service import get_mqtt_bridge
from blanky.speech_service import get_tts_voice_options, set_tts_voice, tts_speak_to_wav
from blanky.voice_worker import VoiceWorker
from blanky.wakeword_service import get_wakeword_service
from blanky.command_parser import command_catalog_text, interpret_online_commands, parse_command


class BlankyController(QObject):
    statusTextChanged = Signal()
    recognizedTextChanged = Signal()
    commTextChanged = Signal()
    commStatusCompactChanged = Signal()
    commDetailsCompactChanged = Signal()
    dateTimeTextChanged = Signal()
    darkModeChanged = Signal()
    monitorLeftTextChanged = Signal()
    monitorEventsTextChanged = Signal()
    listeningChanged = Signal()
    languageChanged = Signal()
    ttsVoiceChanged = Signal()
    ttsVoiceOptionsChanged = Signal()
    ttsSpeedChanged = Signal()
    canRepeatTtsChanged = Signal()
    commandCatalogChanged = Signal()
    soundEnabledChanged = Signal()
    soundVolumeChanged = Signal()
    audioInputPresetChanged = Signal()
    micSensitivityChanged = Signal()
    micWaitForSpeechChanged = Signal()
    micMinCommandChanged = Signal()
    micSilenceHoldChanged = Signal()
    micMaxGainChanged = Signal()
    micHighpassEnabledChanged = Signal()
    micNoiseGateEnabledChanged = Signal()
    micNoiseReductionEnabledChanged = Signal()
    audioSettingsModeChanged = Signal()
    audioSelectedProfileChanged = Signal()
    audioDiagnosticLogTextChanged = Signal()
    stateCompactChanged = Signal()
    textCommandsResolved = Signal(object, str)
    textCommandsFailed = Signal()

    _SENSITIVITY_FACTOR_MIN = 1.20
    _SENSITIVITY_FACTOR_MAX = 2.60
    _STATE_ORDER = [
        "start",
        "mode_fast",
        "mode_ideal",
        "mode_manual",
        "mode_change",
        "motor_1",
        "motor_2",
        "motor_3",
        "cyl_a",
        "cyl_b",
        "cyl_c",
        "cyl_d",
        "light_green",
        "light_red",
        "robot_metal",
        "robot_nonmetal",
    ]
    _TEXT = {
        "pt": {
            "language_status": "🇵🇹 Pronto — Português (PT)",
            "language_status_en": "🇬🇧 Pronto — Inglês (EN)",
            "text_status": "Comando por texto",
            "text_online_interpreting": "A perceber...",
            "text_no_commands": "Não percebi",
            "text_online_error": "Não percebi",
            "button_status": "Botão selecionado",
            "mqtt_status": "Comando pelo telemóvel",
            "voice_command_status": "Comando por voz",
            "voice_no_speech_status": "Não ouvi nada",
            "voice_listening": "A ouvir...",
            "voice_recognizing": "A perceber...",
            "voice_error": "Ocorreu um erro",
            "awaiting_interaction": "Pode começar.",
            "text_received_response": "A perceber...",
            "voice_prompt": "Fale agora.",
            "no_command_response": "Tente novamente.",
            "no_speech_response": "Fale novamente.",
            "system_reset_status": "Sistema reiniciado",
            "shutting_down_status": "A desligar...",
            "starting_status": "A preparar...",
            "export_error": "Erro ao exportar: {error}",
            "exported": "Eventos exportados: {path}",
            "exported_tts": "Eventos exportados.",
            "audio_exported": "Registos de áudio exportados: {path}",
            "audio_exported_tts": "Registos de áudio exportados.",
            "no_audio": "(sem áudio detetado)",
            "error": "Erro: {error}",
            "connected": "Ligado",
            "offline": "Offline",
            "idle": "Sem movimento",
            "microphone": "Microfone",
            "phone": "MQTT Telemóvel",
            "audio_diagnostic": "Diagnóstico de áudio",
            "components_state": "Estado dos Componentes",
            "error_opcua": "Erro OPCUA",
            "error_wakeword": "Erro WakeWord",
            "simple": "Simples",
            "balanced": "Equilibrado",
            "noisy": "Ruidoso",
            "custom": "Personalizado",
            "events_title": "Eventos Blanky",
            "event_report_title": "Relat\u00f3rio de eventos Blanky",
            "voice_preview": "Ol\u00e1, eu sou {voice}.",
            "system_reset": "Sistema reiniciado.",
            "system_shutdown": "A desligar.",
            "no_change_stop": "Sem alteração: sistema já estava parado.",
            "no_change_inactive": "Sem alteração: {command} já estava desativado.",
            "no_change_active": "Sem alteração: {command} já estava ativo.",
            "invalid_unknown": "Comando não reconhecido.",
            "invalid_audio": "Não foi detetado áudio.",
            "workflow_before_mode": "Não pode ainda. Depois de START deve escolher um modo: rápido, ideal ou manual. Pode também dizer STOP.",
            "workflow_change_mode": "Modo de troca ativo. Escolha agora: rápido, ideal ou manual. Ou STOP.",
            "workflow_direct_mode": "Não pode mudar diretamente de modo. Use MODE_CHANGE e depois escolha o novo modo, ou diga STOP.",
            "workflow_components": "Neste modo não pode comandar componentes. Use MODE_CHANGE ou STOP.",
            "workflow_manual": "No modo manual não pode escolher rápido/ideal diretamente. Use MODE_CHANGE primeiro.",
        },
        "en": {
            "language_status": "🇬🇧 Ready — English (EN)",
            "language_status_en": "🇵🇹 Ready — Portuguese (PT)",
            "text_status": "Text command",
            "text_online_interpreting": "Understanding...",
            "text_no_commands": "I did not understand",
            "text_online_error": "I did not understand",
            "button_status": "Button selected",
            "mqtt_status": "Command by phone",
            "voice_command_status": "Voice command",
            "voice_no_speech_status": "I did not hear anything",
            "voice_listening": "Listening...",
            "voice_recognizing": "Understanding...",
            "voice_error": "An error occurred",
            "awaiting_interaction": "You can start.",
            "text_received_response": "Understanding...",
            "voice_prompt": "Speak now.",
            "no_command_response": "Try again.",
            "no_speech_response": "Please speak again.",
            "system_reset_status": "System reset",
            "shutting_down_status": "Shutting down...",
            "starting_status": "Getting ready...",
            "export_error": "Export error: {error}",
            "exported": "Events exported: {path}",
            "exported_tts": "Events exported.",
            "audio_exported": "Audio logs exported: {path}",
            "audio_exported_tts": "Audio logs exported.",
            "no_audio": "(no audio detected)",
            "error": "Error: {error}",
            "connected": "Connected",
            "offline": "Offline",
            "idle": "No traffic",
            "microphone": "Microphone",
            "phone": "MQTT Phone",
            "audio_diagnostic": "Audio diagnostic",
            "components_state": "Component state",
            "error_opcua": "OPCUA error",
            "error_wakeword": "WakeWord error",
            "simple": "Simple",
            "balanced": "Balanced",
            "noisy": "Noisy",
            "custom": "Custom",
            "events_title": "Blanky Events",
            "event_report_title": "Blanky event report",
            "voice_preview": "Hello, I am {voice}.",
            "system_reset": "System reset.",
            "system_shutdown": "Shutting down.",
            "no_change_stop": "No change: system was already stopped.",
            "no_change_inactive": "No change: {command} was already inactive.",
            "no_change_active": "No change: {command} was already active.",
            "invalid_unknown": "Command not recognized.",
            "invalid_audio": "No audio was detected.",
            "workflow_before_mode": "Not allowed yet. After START, choose a mode: fast, ideal or manual. You can also say STOP.",
            "workflow_change_mode": "Mode change is active. Choose now: fast, ideal or manual. Or STOP.",
            "workflow_direct_mode": "Direct mode switch is not allowed. Use MODE_CHANGE and then select the new mode, or say STOP.",
            "workflow_components": "In this mode you cannot control components. Use MODE_CHANGE or STOP.",
            "workflow_manual": "In manual mode you cannot switch directly to fast or ideal. Use MODE_CHANGE first.",
        },
    }

    def __init__(self):
        super().__init__()
        self._status_text = self._language_status("pt")
        self._recognized_text = self._tr("awaiting_interaction", lang="pt")
        self._comm_text = ""
        self._comm_status_compact = ""
        self._comm_details_compact = ""
        self._datetime_text = ""
        self._dark_mode = True
        self._monitor_left_text = ""
        self._monitor_events_text = ""
        self._monitor_events_rich_text = ""
        self._language = "pt"
        self._tts_voice = set_tts_voice("", self._language)
        self._tts_speed = 1.0
        self._last_tts_text = ""
        self._sound_enabled = is_audio_output_enabled()
        self._sound_volume = get_audio_output_volume()
        self._audio_input_preset = ""
        self._audio_settings_mode = "auto"
        self._audio_selected_profile = "simple"
        self._audio_diagnostic_entries: list[dict] = []
        self._mic_sensitivity = 50.0
        self._mic_wait_for_speech = 0.70
        self._mic_min_command = 0.55
        self._mic_silence_hold = 0.35
        self._mic_max_gain = 4.50
        self._mic_highpass_enabled = False
        self._mic_noise_gate_enabled = False
        self._mic_noise_reduction_enabled = False
        self._state_compact = ""
        self._listening = False
        self._sync_audio_input_state(force=True)
        self._audio_selected_profile = get_audio_input_preset()

        self._bridge = get_mqtt_bridge()
        self._bridge.set_ui_lang(self._language)
        self._wakeword = get_wakeword_service()
        self._wakeword.start()
        self._worker = None
        self._last_event_id_seen = 0

        self._tts_queue: queue.Queue[object] = queue.Queue()
        self._text_command_queue: list[str] = []
        self._text_command_timer = QTimer(self)
        self._text_command_timer.setSingleShot(True)
        self._text_command_timer.timeout.connect(self._execute_next_text_command)
        self.textCommandsResolved.connect(self._queue_text_commands)
        self.textCommandsFailed.connect(self._handle_text_online_error)
        self._panel_tts_path = os.path.join(AUDIO_DIR, "tts_panel.wav")
        self._tts_thread = threading.Thread(target=self._panel_tts_loop, daemon=True)
        self._tts_thread.start()

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()
        self._refresh()

    # ---------- QML Properties ----------
    @Property(str, notify=statusTextChanged)
    def statusText(self):
        return self._status_text

    @Property(str, notify=recognizedTextChanged)
    def recognizedText(self):
        return self._recognized_text

    @Property(str, notify=commTextChanged)
    def commText(self):
        return self._comm_text

    @Property(str, notify=commStatusCompactChanged)
    def commStatusCompact(self):
        return self._comm_status_compact

    @Property(str, notify=commDetailsCompactChanged)
    def commDetailsCompact(self):
        return self._comm_details_compact

    @Property(str, notify=dateTimeTextChanged)
    def dateTimeText(self):
        return self._datetime_text

    @Property(bool, notify=darkModeChanged)
    def darkMode(self):
        return self._dark_mode

    @Property(str, notify=monitorLeftTextChanged)
    def monitorLeftText(self):
        return self._monitor_left_text

    @Property(str, notify=monitorEventsTextChanged)
    def monitorEventsText(self):
        return self._monitor_events_text

    @Property(str, notify=monitorEventsTextChanged)
    def monitorEventsRichText(self):
        return self._monitor_events_rich_text

    @Property(bool, notify=listeningChanged)
    def listening(self):
        return self._listening

    @Property(str, notify=languageChanged)
    def language(self):
        return self._language

    @Property(str, notify=ttsVoiceChanged)
    def ttsVoice(self):
        return self._tts_voice

    @Property(str, notify=ttsVoiceOptionsChanged)
    def ttsVoiceOptions(self):
        return "|".join(get_tts_voice_options(self._language))

    @Property(float, notify=ttsSpeedChanged)
    def ttsSpeed(self):
        return self._tts_speed

    @Property(bool, notify=canRepeatTtsChanged)
    def canRepeatTts(self):
        return bool(self._last_tts_text)

    @Property(str, notify=commandCatalogChanged)
    def commandCatalogText(self):
        return command_catalog_text(self._language)

    @Property(QUrl, constant=True)
    def defaultExportFolder(self):
        """Expose the project's exports folder as the initial folder-dialog location."""
        export_dir = os.path.abspath(os.path.join(os.getcwd(), "exports"))
        os.makedirs(export_dir, exist_ok=True)
        return QUrl.fromLocalFile(export_dir)

    @Property(bool, notify=soundEnabledChanged)
    def soundEnabled(self):
        return self._sound_enabled

    @Property(float, notify=soundVolumeChanged)
    def soundVolume(self):
        return float(self._sound_volume)

    @Property(str, notify=audioInputPresetChanged)
    def audioInputPreset(self):
        return self._audio_input_preset

    @Property(float, notify=micSensitivityChanged)
    def micSensitivity(self):
        return float(self._mic_sensitivity)

    @Property(float, notify=micWaitForSpeechChanged)
    def micWaitForSpeech(self):
        return float(self._mic_wait_for_speech)

    @Property(float, notify=micMinCommandChanged)
    def micMinCommand(self):
        return float(self._mic_min_command)

    @Property(float, notify=micSilenceHoldChanged)
    def micSilenceHold(self):
        return float(self._mic_silence_hold)

    @Property(float, notify=micMaxGainChanged)
    def micMaxGain(self):
        return float(self._mic_max_gain)

    @Property(bool, notify=micHighpassEnabledChanged)
    def micHighpassEnabled(self):
        return self._mic_highpass_enabled

    @Property(bool, notify=micNoiseGateEnabledChanged)
    def micNoiseGateEnabled(self):
        return self._mic_noise_gate_enabled

    @Property(bool, notify=micNoiseReductionEnabledChanged)
    def micNoiseReductionEnabled(self):
        return self._mic_noise_reduction_enabled

    @Property(str, notify=audioSettingsModeChanged)
    def audioSettingsMode(self):
        return self._audio_settings_mode

    @Property(str, notify=audioSelectedProfileChanged)
    def audioSelectedProfile(self):
        return self._audio_selected_profile

    @Property(str, notify=audioDiagnosticLogTextChanged)
    def audioDiagnosticLogText(self):
        if not self._audio_diagnostic_entries:
            return ""

        id_w = 5
        time_w = 8
        capture_w = 8
        transcript_w = 28
        command_w = 14
        result_w = 9
        duration_w = 7
        lines = []
        for index, entry in enumerate(self._audio_diagnostic_entries, start=1):
            transcript_lines = textwrap.wrap(
                str(entry["text"]), width=transcript_w,
                break_long_words=True, break_on_hyphens=False,
            ) or [""]
            prefix = (
                f"[{index:03d}]".ljust(id_w) + " | "
                + str(entry["time"]).ljust(time_w) + " | "
                + f"{float(entry['capture']):.2f}s".rjust(capture_w) + " | "
                + transcript_lines[0].ljust(transcript_w) + " | "
                + str(entry["command"]).ljust(command_w) + " | "
                + str(entry.get("result", "--")).ljust(result_w) + " | "
                + f"{float(entry.get('duration', 0.0)):.2f}s".rjust(duration_w)
            )
            lines.append(prefix)

            continuation_prefix = (
                " ".ljust(id_w) + " | " + " ".ljust(time_w) + " | "
                + " ".ljust(capture_w) + " | "
            )
            continuation_suffix = (
                " | " + " ".ljust(command_w) + " | "
                + " ".ljust(result_w) + " | " + " ".ljust(duration_w)
            )
            for transcript_line in transcript_lines[1:]:
                lines.append(continuation_prefix + transcript_line.ljust(transcript_w) + continuation_suffix)
        return "\n".join(lines)

    @Property(str, notify=audioDiagnosticLogTextChanged)
    def audioDiagnosticHeaderText(self):
        headers = (
            ("ID", "Hora", "Capta\u00e7\u00e3o", "Transcri\u00e7\u00e3o", "Comando", "Resultado", "Dura\u00e7\u00e3o")
            if self._language == "pt"
            else ("ID", "Time", "Capture", "Transcript", "Command", "Result", "Duration")
        )
        widths = (5, 8, 8, 28, 14, 9, 7)
        return " | ".join(value.ljust(width) for value, width in zip(headers, widths))

    @Property(str, notify=audioDiagnosticLogTextChanged)
    def audioDiagnosticDividerText(self):
        return " | ".join("-" * width for width in (5, 8, 8, 28, 14, 9, 7))

    @Property(str, notify=stateCompactChanged)
    def stateCompact(self):
        return self._state_compact

    # ---------- QML Slots ----------
    @Slot()
    def toggleTheme(self):
        self._dark_mode = not self._dark_mode
        self.darkModeChanged.emit()

    @Slot(str)
    def setLanguage(self, lang: str):
        if lang not in {"pt", "en"}:
            return
        if self._language == lang:
            return
        self._language = lang
        self._bridge.set_ui_lang(self._language)
        self._tts_voice = set_tts_voice(self._tts_voice, self._language)
        self.languageChanged.emit()
        self.ttsVoiceOptionsChanged.emit()
        self.ttsVoiceChanged.emit()
        self.commandCatalogChanged.emit()
        self.audioDiagnosticLogTextChanged.emit()

        if not self._listening:
            self._set_status(self._language_status(self._language))
            awaiting_values = {
                self._tr("awaiting_interaction", lang="pt"),
                self._tr("awaiting_interaction", lang="en"),
            }
            if self._recognized_text in awaiting_values:
                self._set_recognized(self._tr("awaiting_interaction"))
        self._refresh()

    @Slot(str)
    def setTtsVoice(self, voice: str):
        selected = set_tts_voice(voice, self._language)
        if selected != self._tts_voice:
            self._tts_voice = selected
            self.ttsVoiceChanged.emit()

    @Slot(str)
    def previewTtsVoice(self, voice: str):
        if voice not in get_tts_voice_options(self._language):
            return
        preview = self._tr("voice_preview", voice=voice.capitalize())
        self._tts_queue.put((preview, voice, self._tts_speed))

    @Slot(float)
    def setTtsSpeed(self, speed: float):
        options = (0.80, 1.00, 1.20)
        selected = min(options, key=lambda item: abs(item - float(speed)))
        if abs(selected - self._tts_speed) > 1e-6:
            self._tts_speed = selected
            self.ttsSpeedChanged.emit()

    @Slot()
    def repeatLastTts(self):
        if self._last_tts_text:
            self._tts_queue.put((self._last_tts_text, self._tts_voice, self._tts_speed))

    @Slot()
    def clearInteraction(self):
        self._set_recognized(self._tr("awaiting_interaction"))
        if not self._listening:
            self._set_status(self._language_status(self._language))

    @Slot()
    def toggleSound(self):
        self._sound_enabled = not self._sound_enabled
        set_audio_output_enabled(self._sound_enabled)
        self.soundEnabledChanged.emit()

    @Slot(float)
    def setSoundVolume(self, value: float):
        set_audio_output_volume(float(value))
        new_v = get_audio_output_volume()
        if abs(float(new_v) - float(self._sound_volume)) > 1e-6:
            self._sound_volume = float(new_v)
            self.soundVolumeChanged.emit()

    @Slot()
    def testBeep(self):
        play_beep()

    @Slot(str)
    def setAudioInputPreset(self, preset: str):
        apply_audio_input_preset(preset)
        self._audio_selected_profile = get_audio_input_preset()
        self._audio_settings_mode = "auto"
        self.audioSelectedProfileChanged.emit()
        self.audioSettingsModeChanged.emit()
        self._sync_audio_input_state()

    @Slot(str)
    def setAudioSettingsMode(self, mode: str):
        target = "manual" if mode == "manual" else "auto"
        if target == "auto":
            apply_audio_input_preset(self._audio_selected_profile)
            self._sync_audio_input_state()
        if self._audio_settings_mode != target:
            self._audio_settings_mode = target
            self.audioSettingsModeChanged.emit()

    @Slot()
    def resetAudioInputSettings(self):
        apply_audio_input_preset("simple")
        self._audio_selected_profile = "simple"
        self._audio_settings_mode = "auto"
        self.audioSelectedProfileChanged.emit()
        self.audioSettingsModeChanged.emit()
        self._sync_audio_input_state()

    @Slot(float)
    def setMicSensitivity(self, value: float):
        update_audio_input_settings(trigger_factor=self._sensitivity_to_trigger_factor(value))
        self._sync_audio_input_state()

    @Slot(float)
    def setMicWaitForSpeech(self, value: float):
        update_audio_input_settings(wait_for_speech_seconds=float(value))
        self._sync_audio_input_state()

    @Slot(float)
    def setMicMinCommand(self, value: float):
        update_audio_input_settings(min_record_seconds=float(value))
        self._sync_audio_input_state()

    @Slot(float)
    def setMicSilenceHold(self, value: float):
        update_audio_input_settings(silence_hold_seconds=float(value))
        self._sync_audio_input_state()

    @Slot(float)
    def setMicMaxGain(self, value: float):
        update_audio_input_settings(max_gain=float(value))
        self._sync_audio_input_state()

    @Slot(bool)
    def setMicHighpassEnabled(self, enabled: bool):
        update_audio_input_settings(highpass_enabled=bool(enabled))
        self._sync_audio_input_state()

    @Slot(bool)
    def setMicNoiseGateEnabled(self, enabled: bool):
        update_audio_input_settings(noise_gate_enabled=bool(enabled))
        self._sync_audio_input_state()

    @Slot(bool)
    def setMicNoiseReductionEnabled(self, enabled: bool):
        update_audio_input_settings(noise_reduction_enabled=bool(enabled))
        self._sync_audio_input_state()

    def _stop_and_flush_audio(self):
        stop_playback()
        while True:
            try:
                self._tts_queue.get_nowait()
            except Exception:
                break

    def _trigger_factor_to_sensitivity(self, factor: float) -> float:
        clamped = max(self._SENSITIVITY_FACTOR_MIN, min(self._SENSITIVITY_FACTOR_MAX, float(factor)))
        span = self._SENSITIVITY_FACTOR_MAX - self._SENSITIVITY_FACTOR_MIN
        if span <= 0:
            return 50.0
        return ((self._SENSITIVITY_FACTOR_MAX - clamped) / span) * 100.0

    def _sensitivity_to_trigger_factor(self, sensitivity: float) -> float:
        clamped = max(0.0, min(100.0, float(sensitivity)))
        span = self._SENSITIVITY_FACTOR_MAX - self._SENSITIVITY_FACTOR_MIN
        return self._SENSITIVITY_FACTOR_MAX - ((clamped / 100.0) * span)

    def _sync_audio_input_state(self, force: bool = False):
        settings = get_audio_input_settings()
        preset = get_audio_input_preset()

        new_sensitivity = self._trigger_factor_to_sensitivity(float(settings.get("trigger_factor", 1.65)))
        new_wait = float(settings.get("wait_for_speech_seconds", 0.70))
        new_min = float(settings.get("min_record_seconds", 0.55))
        new_silence = float(settings.get("silence_hold_seconds", 0.35))
        new_gain = float(settings.get("max_gain", 4.50))
        new_highpass = bool(settings.get("highpass_enabled", False))
        new_noise_gate = bool(settings.get("noise_gate_enabled", False))
        new_noise_reduction = bool(settings.get("noise_reduction_enabled", False))

        if force or self._audio_input_preset != preset:
            self._audio_input_preset = preset
            self.audioInputPresetChanged.emit()
        if force or abs(self._mic_sensitivity - new_sensitivity) > 1e-6:
            self._mic_sensitivity = new_sensitivity
            self.micSensitivityChanged.emit()
        if force or abs(self._mic_wait_for_speech - new_wait) > 1e-6:
            self._mic_wait_for_speech = new_wait
            self.micWaitForSpeechChanged.emit()
        if force or abs(self._mic_min_command - new_min) > 1e-6:
            self._mic_min_command = new_min
            self.micMinCommandChanged.emit()
        if force or abs(self._mic_silence_hold - new_silence) > 1e-6:
            self._mic_silence_hold = new_silence
            self.micSilenceHoldChanged.emit()
        if force or abs(self._mic_max_gain - new_gain) > 1e-6:
            self._mic_max_gain = new_gain
            self.micMaxGainChanged.emit()
        if force or self._mic_highpass_enabled != new_highpass:
            self._mic_highpass_enabled = new_highpass
            self.micHighpassEnabledChanged.emit()
        if force or self._mic_noise_gate_enabled != new_noise_gate:
            self._mic_noise_gate_enabled = new_noise_gate
            self.micNoiseGateEnabledChanged.emit()
        if force or self._mic_noise_reduction_enabled != new_noise_reduction:
            self._mic_noise_reduction_enabled = new_noise_reduction
            self.micNoiseReductionEnabledChanged.emit()

    @Slot(str)
    def submitTextCommand(self, text: str):
        self.submitTextCommands(text, "offline")

    @Slot(str, str)
    def submitTextCommands(self, text: str, mode: str):
        raw = (text or "").strip()
        if not raw:
            return
        self._set_recognized(self._tr("text_received_response"))

        if (mode or "offline").strip().lower() == "online":
            self._set_status(self._tr("text_online_interpreting"))
            threading.Thread(target=self._resolve_online_text, args=(raw,), daemon=True).start()
            return

        commands = []
        for phrase in re.split(r"[\n;]+", raw):
            phrase = phrase.strip()
            if phrase:
                command, _ = parse_command(phrase, self._language)
                commands.append(command)
        self._queue_text_commands(commands, raw)

    def _resolve_online_text(self, raw: str):
        try:
            commands = interpret_online_commands(raw, self._language)
        except Exception:
            self.textCommandsFailed.emit()
            return
        self.textCommandsResolved.emit(commands, raw)

    @Slot()
    def _handle_text_online_error(self):
        self._set_status(self._tr("text_online_error"))
        self._set_recognized(self._tr("no_command_response"))

    @Slot(object, str)
    def _queue_text_commands(self, commands, raw: str):
        valid_commands = [str(command).upper() for command in commands if str(command).strip()]
        if not valid_commands:
            self._set_status(self._tr("text_no_commands"))
            self._set_recognized(self._tr("no_command_response"))
            return

        self._stop_and_flush_audio()
        self._set_recognized(self._tr("text_received_response"))
        self._text_command_queue.extend(valid_commands)
        if not self._text_command_timer.isActive():
            self._execute_next_text_command()

    def _execute_next_text_command(self):
        if not self._text_command_queue:
            return

        command = self._text_command_queue.pop(0)
        if command in {"UNKNOWN", "NO_AUDIO"}:
            _, response = self._bridge.process_command(command, self._language, source="text")
            self._set_status(self._tr("text_no_commands"))
            self._set_recognized(self._tr("no_command_response"))
            if response:
                self._enqueue_tts(response)
            return
        _, response = self._bridge.process_command(command, self._language, source="text")
        self._set_command_interaction("text_status", command)
        if response:
            self._enqueue_tts(response)
        if self._text_command_queue:
            self._text_command_timer.start(300)

    @Slot(str)
    def submitButtonCommand(self, command: str):
        command = (command or "").strip().upper()
        if not command:
            return
        accepted, mqtt_message = self._bridge.process_command(
            command,
            self._language,
            source="button",
        )
        response = mqtt_message or (self._bridge.response_for_command(command, self._language) if accepted else "")
        self._set_command_interaction("button_status", command)
        if response:
            self._enqueue_tts(response)

    @Slot()
    def resetSystem(self):
        self._stop_and_flush_audio()
        _, response = self._bridge.reset_system(self._language, source="button")
        self._set_recognized(self._tr("system_reset"))
        self._set_status(self._tr("system_reset_status"))
        self._enqueue_tts(response)

    @Slot()
    def shutdownApplication(self):
        self._stop_and_flush_audio()
        self._bridge.shutdown_system(self._language, source="button")
        self._set_recognized(self._tr("system_shutdown"))
        self._set_status(self._tr("shutting_down_status"))
        # The QML transition already gives the operator a three-second shutdown notice.
        QTimer.singleShot(80, QCoreApplication.quit)

    @Slot(str)
    def exportEvents(self, fmt: str):
        self.exportEventsTo(fmt, "")

    @Slot(str, str)
    def exportEventsTo(self, fmt: str, folder: str):
        fmt = (fmt or "csv").strip().lower()
        events = self._bridge.get_snapshot().get("events", [])
        try:
            path = self._write_events_export(events, fmt, folder)
        except Exception as exc:
            self._set_status(self._tr("export_error", error=exc))
            return

        self._set_status(self._tr("exported", path=path))
        self._enqueue_tts(self._tr("exported_tts"))

    @Slot(str, str)
    def exportAudioDiagnosticsTo(self, fmt: str, folder: str):
        fmt = (fmt or "csv").strip().lower()
        try:
            path = self._write_audio_diagnostics_export(fmt, folder)
        except Exception as exc:
            self._set_status(self._tr("export_error", error=exc))
            return

        self._set_status(self._tr("audio_exported", path=path))
        self._enqueue_tts(self._tr("audio_exported_tts"))

    @Slot()
    def startVoice(self):
        if self._listening:
            return

        try:
            self._stop_and_flush_audio()
            self._wakeword.set_paused(True)
            self._set_listening(True)
            self._set_recognized(self._tr("voice_prompt"))
            self._set_status(self._tr("starting_status"))
            play_beep()

            self._worker = VoiceWorker(lang=self._language, tts_speed=self._tts_speed)
            self._worker.status.connect(self._set_status)
            self._worker.recognized.connect(self._on_recognized)
            self._worker.commandRecognized.connect(self._on_voice_command)
            self._worker.diagnostic.connect(self._append_audio_diagnostic)
            self._worker.spoken.connect(self._remember_tts_text)
            self._worker.done.connect(self._on_done)
            self._worker.start()
        except Exception as exc:
            self._worker = None
            self._set_listening(False)
            self._wakeword.set_paused(False)
            self._set_status(self._tr("error", error=exc))

    # ---------- Internal ----------
    def _set_status(self, text: str):
        if self._status_text != text:
            self._status_text = text
            self.statusTextChanged.emit()

    def _set_recognized(self, text: str):
        if self._recognized_text != text:
            self._recognized_text = text
            self.recognizedTextChanged.emit()

    def _set_comm(self, text: str):
        if self._comm_text != text:
            self._comm_text = text
            self.commTextChanged.emit()

    def _set_comm_status_compact(self, text: str):
        if self._comm_status_compact != text:
            self._comm_status_compact = text
            self.commStatusCompactChanged.emit()

    def _set_comm_details_compact(self, text: str):
        if self._comm_details_compact != text:
            self._comm_details_compact = text
            self.commDetailsCompactChanged.emit()

    def _set_datetime(self, text: str):
        if self._datetime_text != text:
            self._datetime_text = text
            self.dateTimeTextChanged.emit()

    def _set_monitor_left_text(self, text: str):
        if self._monitor_left_text != text:
            self._monitor_left_text = text
            self.monitorLeftTextChanged.emit()

    def _set_monitor_events_text(self, text: str, rich_text: str):
        if self._monitor_events_text != text or self._monitor_events_rich_text != rich_text:
            self._monitor_events_text = text
            self._monitor_events_rich_text = rich_text
            self.monitorEventsTextChanged.emit()

    def _set_listening(self, value: bool):
        if self._listening != value:
            self._listening = value
            self.listeningChanged.emit()

    def _tr(self, key: str, lang: str | None = None, **values) -> str:
        table = self._TEXT.get(lang or self._language, self._TEXT["pt"])
        text = table.get(key, self._TEXT["pt"].get(key, key))
        return text.format(**values)

    def _language_status(self, lang: str) -> str:
        return self._tr("language_status", lang=lang)

    def _friendly_command_request(self, command: str, lang: str | None = None) -> str:
        """Translate internal command identifiers into safe, user-facing requests."""
        is_pt = (lang or self._language) == "pt"
        canonical = (command or "").strip().upper()
        direct = {
            "START": ("Iniciar sistema.", "Start system."),
            "STOP": ("Parar sistema.", "Stop system."),
            "MODE_FAST": ("Modo rápido escolhido.", "Fast mode selected."),
            "MODE_IDEAL": ("Modo ideal escolhido.", "Ideal mode selected."),
            "MODE_MANUAL": ("Modo manual escolhido.", "Manual mode selected."),
            "MODE_UNSPEC": ("Escolha outro modo.", "Choose another mode."),
            "MODE_CHANGE": ("Escolha outro modo.", "Choose another mode."),
            "GREEN_ON": ("Acender luz verde.", "Turn on green light."),
            "GREEN_OFF": ("Apagar luz verde.", "Turn off green light."),
            "RED_ON": ("Acender luz vermelha.", "Turn on red light."),
            "RED_OFF": ("Apagar luz vermelha.", "Turn off red light."),
            "ROBOT_TO_METAL": ("Enviar robô para metal.", "Send robot to metal."),
            "ROBOT_TO_NONMETAL": ("Enviar robô para não metal.", "Send robot to non-metal."),
        }
        if canonical in direct:
            return direct[canonical][0 if is_pt else 1]

        motor = re.fullmatch(r"MOTOR_(\d+)_(ON|OFF)", canonical)
        if motor:
            number, action = motor.groups()
            if is_pt:
                return f"{'Ligar' if action == 'ON' else 'Desligar'} Motor {number}."
            return f"Turn {'on' if action == 'ON' else 'off'} Motor {number}."

        cylinder = re.fullmatch(r"CYL_([A-D])_(EXTEND|RETRACT)", canonical)
        if cylinder:
            letter, action = cylinder.groups()
            if is_pt:
                return f"{'Avançar' if action == 'EXTEND' else 'Recuar'} Cilindro {letter}."
            return f"{'Extend' if action == 'EXTEND' else 'Retract'} Cylinder {letter}."

        return self._tr("no_command_response", lang=lang)

    def _set_command_interaction(self, status_key: str, command: str):
        self._set_status(self._tr(status_key))
        self._set_recognized(self._friendly_command_request(command))

    def _on_voice_command(self, command: str):
        canonical = (command or "").strip().upper()
        if canonical == "NO_AUDIO":
            self._set_status(self._tr("voice_no_speech_status"))
            self._set_recognized(self._tr("no_speech_response"))
            return
        if canonical in {"UNKNOWN", ""}:
            self._set_status(self._tr("text_no_commands"))
            self._set_recognized(self._tr("no_command_response"))
            return
        self._set_command_interaction("voice_command_status", canonical)

    def _on_recognized(self, text: str):
        if text:
            self._set_recognized(self._repair_display_text(text))

    @staticmethod
    def _repair_display_text(value: str) -> str:
        """Repair UTF-8 text that was incorrectly decoded as Latin-1 upstream."""
        text = str(value or "")
        if not any(marker in text for marker in ("Ã", "Â", "â")):
            return text
        try:
            return text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text

    def _append_audio_diagnostic(self, entry: dict):
        item = dict(entry or {})
        item.setdefault("time", datetime.now().strftime("%H:%M:%S"))
        item.setdefault("language", self._language)
        item.setdefault("capture", 0.0)
        item.setdefault("stt", 0.0)
        item.setdefault("end", "--")
        item.setdefault("command", "--")
        item.setdefault("text", self._tr("no_audio"))
        item.setdefault("result", "--")
        item.setdefault("duration", 0.0)
        item["text"] = self._repair_display_text(item["text"])
        self._audio_diagnostic_entries.append(item)
        self.audioDiagnosticLogTextChanged.emit()

    def _on_done(self):
        self._worker = None
        self._set_listening(False)
        self._wakeword.set_paused(False)

    def _panel_tts_loop(self):
        while True:
            job = self._tts_queue.get()
            voice = None
            speed = self._tts_speed
            if isinstance(job, tuple):
                text = job[0]
                if len(job) > 1:
                    voice = job[1]
                if len(job) > 2:
                    speed = job[2]
            else:
                text = job
            if not text:
                continue
            try:
                tts_speak_to_wav(
                    text,
                    self._panel_tts_path,
                    voice=voice,
                    speed=speed,
                    lang=self._language,
                )
                play_wav(self._panel_tts_path)
            except Exception:
                pass

    def _remember_tts_text(self, text: str):
        if not text:
            return
        self._last_tts_text = str(text)
        self.canRepeatTtsChanged.emit()

    def _enqueue_tts(self, text: str):
        if not text:
            return
        self._remember_tts_text(text)
        self._tts_queue.put((str(text), self._tts_voice, self._tts_speed))

    def _comm_badge(self, label: str, state: str) -> str:
        palette = {
            "ok": ("#48d66b", self._tr("connected")),
            "off": ("#ff6b6b", self._tr("offline")),
            "idle": ("#f8c25d", self._tr("idle")),
        }
        color, text = palette.get(state, ("#8fa8b8", state))
        return (
            f"<span style='color:{color}; font-weight:700;'>●</span> "
            f"<span><b>{html.escape(label)}</b> {html.escape(text)}</span>"
        )

    def _preset_label(self, preset: str) -> str:
        mapping = {
            "simple": self._tr("simple"),
            "balanced": self._tr("balanced"),
            "noisy": self._tr("noisy"),
            "custom": self._tr("custom"),
        }
        return mapping.get((preset or "").strip().lower(), preset or "--")

    def _filter_status(self, enabled: bool) -> str:
        return (
            "<span style='color:#48d66b; font-weight:700;'>ON</span>"
            if enabled
            else "<span style='color:#8fa8b8;'>OFF</span>"
        )

    def _build_comm_line(self, health: dict) -> str:
        wake = self._wakeword.health()
        alerts = []
        if health.get("opcua_last_error"):
            alerts.append(
                f"OPC UA · {self._communication_error_text(str(health.get('opcua_last_error')))}"
            )
        if WAKEWORD_ENABLED and wake.get("last_error"):
            alerts.append(
                f"Wake Word · {self._communication_error_text(str(wake.get('last_error')))}"
            )
        return "   |   ".join(alerts)

    def _communication_error_text(self, raw_error: str) -> str:
        normalized = (raw_error or "").strip().lower()
        if "timed out" in normalized or "timeout" in normalized:
            return (
                "Tempo limite de comunicação excedido."
                if self._language == "pt"
                else "Communication timeout exceeded."
            )
        return (raw_error or "").strip()

    def _build_comm_status_compact(self, health: dict) -> str:
        wake = self._wakeword.health()
        states = {
            "microphone": "connected" if health.get("microphone_ready") else "offline",
            "mqtt_base": "connected" if health.get("mqtt_base_connected") else "offline",
            "mqtt_phone": "communicating" if health.get("mqtt_panel_active") else "silent",
            "opcua": "connected" if health.get("opcua_connected") else "offline",
        }
        if WAKEWORD_ENABLED:
            states["wakeword"] = "connected" if wake.get("enabled") and wake.get("running") else "offline"
        return "|".join(f"{key}={value}" for key, value in states.items())

    def _build_comm_details_compact(self, health: dict) -> str:
        is_pt = self._language == "pt"
        seconds = health.get("mqtt_panel_last_rx_seconds")
        if seconds is None:
            mqtt_phone = "A aguardar mensagens" if is_pt else "Waiting for messages"
        elif seconds < 1:
            mqtt_phone = "Última mensagem agora" if is_pt else "Last message now"
        else:
            whole_seconds = int(seconds)
            mqtt_phone = (
                f"Última mensagem há {whole_seconds} s"
                if is_pt
                else f"Last message {whole_seconds} s ago"
            )
        details = {
            "microphone": "A aguardar voz" if is_pt else "Waiting for voice",
            "mqtt_base": "Ligação ao servidor" if is_pt else "Server connection",
            "mqtt_phone": mqtt_phone,
            "opcua": (
                "Ligação ao PLC" if health.get("opcua_connected") else "Sem ligação ao PLC"
            ) if is_pt else (
                "PLC connection" if health.get("opcua_connected") else "No PLC connection"
            ),
        }
        return "|".join(f"{key}={value}" for key, value in details.items())

    def _state_icon(self, key: str, value: int) -> str:
        base_color = "#8fa8b8" if not value else "#63cbff"
        labels = {
            "start": "▶" if value else "⏸",
            "mode_fast": "⚡",
            "mode_ideal": "🎯",
            "mode_manual": "🕹",
            "mode_change": "🔁",
            "motor_1": "⚙",
            "motor_2": "⚙",
            "motor_3": "⚙",
            "cyl_a": "▰",
            "cyl_b": "▰",
            "cyl_c": "▰",
            "cyl_d": "▰",
            "light_green": "●",
            "light_red": "●",
            "robot_metal": "🤖",
            "robot_nonmetal": "🤖",
        }
        color_overrides = {
            "light_green": "#48d66b" if value else "#4e6f58",
            "light_red": "#ff5c5c" if value else "#7d5151",
            "start": "#3bd67f" if value else "#8fa8b8",
        }
        color = color_overrides.get(key, base_color)
        label = labels.get(key, "ST")
        return (
            f"<span style='display:inline-block; min-width:22px; text-align:center; "
            f"color:{color}; font-weight:700;'>{html.escape(label)}</span>"
        )

    def _build_monitor_left_text(self, snapshot: dict, health: dict) -> str:
        state = snapshot.get("state", {})
        mic = audio_info()
        diag = mic.get("last_record_diag", {}) or {}
        lines = ["<div style='font-family:Segoe UI, Noto Sans, sans-serif; font-size:13px; line-height:1.45;'>"]
        lines.append("<div style='color:#63cbff; font-size:15px; font-weight:700;'>Áudio Diagnóstico</div>")
        lines.append(
            f"<div style='margin-top:6px;'><b>Dispositivo:</b> {html.escape(str(mic.get('input_device')))}"
            f" &nbsp; <b>Sample rate:</b> {html.escape(str(mic.get('sample_rate')))} Hz</div>"
        )
        if diag:
            settings = diag.get("audio_input_settings", {}) or {}
            lines.append(
                f"<div style='margin-top:8px;'><b>Preset ativo:</b> {html.escape(self._preset_label(str(diag.get('audio_input_preset', mic.get('input_preset')))))}"
                f" &nbsp; <b>Fim da captação:</b> {html.escape(str(diag.get('end_reason') or '--'))}</div>"
            )
            lines.append(
                "<div style='margin-top:6px;'><b>Duração</b> "
                "total={:.2f}s | fala={:.2f}s | espera={:.2f}s | pre-roll={}ms</div>".format(
                    float(diag.get("total_duration_s") or 0.0),
                    float(diag.get("speech_duration_s") or 0.0),
                    float(diag.get("waited_for_speech_s") or 0.0),
                    int(diag.get("pre_roll_ms") or 0),
                )
            )
            lines.append(
                "<div style='margin-top:4px;'><b>Níveis RMS</b> "
                "ruído={:.5f} | desvio={:.5f} | trigger={:.5f} | release={:.5f}</div>".format(
                    float(diag.get("noise_floor_rms") or 0.0),
                    float(diag.get("noise_std_rms") or 0.0),
                    float(diag.get("trigger_rms") or 0.0),
                    float(diag.get("release_rms") or 0.0),
                )
            )
            lines.append(
                "<div style='margin-top:4px;'><b>Captação</b> "
                "fallback={} | pico={:.5f} | ganho aplicado={:.2f}x</div>".format(
                    "sim" if bool(diag.get("fallback_started")) else "não",
                    float(diag.get("captured_peak") or 0.0),
                    float(diag.get("applied_gain") or 1.0),
                )
            )
            lines.append(
                "<div style='margin-top:8px;'><b>Ajuste do microfone</b> "
                "sensibilidade={:.0f} | espera={:.2f}s | mínimo={:.2f}s | silêncio={:.2f}s | ganho máx={:.2f}x</div>".format(
                    self._trigger_factor_to_sensitivity(float(settings.get("trigger_factor", 1.65))),
                    float(settings.get("wait_for_speech_seconds") or 0.0),
                    float(settings.get("min_record_seconds") or 0.0),
                    float(settings.get("silence_hold_seconds") or 0.0),
                    float(settings.get("max_gain") or 0.0),
                )
            )
            lines.append(
                "<div style='margin-top:4px;'><b>Filtros</b> "
                f"corta-graves={self._filter_status(bool(diag.get('highpass_enabled')))} | "
                f"noise gate={self._filter_status(bool(diag.get('noise_gate_enabled')))} | "
                f"redução de ruído={self._filter_status(bool(diag.get('noise_reduction_enabled')))} | "
                "fator={:.2f}</div>".format(float(diag.get("noise_subtract_factor") or 0.0))
            )
        else:
            lines.append(
                "<div style='margin-top:8px; color:#8fa8b8;'>Ainda não existe amostra gravada nesta sessão.</div>"
            )

        lines.append("<div style='margin-top:16px; color:#63cbff; font-size:15px; font-weight:700;'>Estado dos Componentes</div>")
        for key in self._STATE_ORDER:
            if key not in state:
                continue
            icon = self._state_icon(key, int(state[key]))
            value_color = "#48d66b" if int(state[key]) else "#8fa8b8"
            lines.append(
                f"<div style='margin-top:4px;'>{icon} <b>{html.escape(str(key))}</b>: "
                f"<span style='color:{value_color}; font-weight:700;'>{int(state[key])}</span></div>"
            )
        lines.append("</div>")
        return "".join(lines)

    def _event_visual_color(self, command: str, accepted: bool) -> str:
        colors = (
            {
                "normal": "#def2ff", "inactive": "#8fa8b8", "error": "#ff6b6b",
                "start": "#48d66b", "fast": "#f8c25d", "ideal": "#d66ad9",
                "manual": "#b7f7d4", "change": "#9dd9ff", "motor": "#63cbff",
                "green": "#48d66b", "red": "#ff5c5c", "robot": "#b7f7d4",
            }
            if self._dark_mode else {
                "normal": "#16384c", "inactive": "#526e7d", "error": "#b32635",
                "start": "#147a3d", "fast": "#8a5b00", "ideal": "#8f3f9e",
                "manual": "#13735e", "change": "#146f9e", "motor": "#126c9f",
                "green": "#147a3d", "red": "#b32635", "robot": "#13735e",
            }
        )
        if not accepted:
            return colors["error"]
        if command == "START":
            return colors["start"]
        if command == "STOP":
            return colors["inactive"]
        if command == "MODE_FAST":
            return colors["fast"]
        if command == "MODE_IDEAL":
            return colors["ideal"]
        if command == "MODE_MANUAL":
            return colors["manual"]
        if command in {"MODE_UNSPEC", "MODE_CHANGE"}:
            return colors["change"]
        if command == "GREEN_ON":
            return colors["green"]
        if command == "RED_ON":
            return colors["red"]
        if command.endswith("_OFF") or command.endswith("_RETRACT"):
            return colors["inactive"]
        if command.startswith("MOTOR_") or command.startswith("CYL_") or command == "ROBOT_TO_METAL":
            return colors["motor"]
        if command == "ROBOT_TO_NONMETAL":
            return colors["robot"]
        return colors["normal"]

    def _build_monitor_event_lines(self, snapshot: dict) -> list[tuple[str, str]]:
        events = snapshot.get("events", [])
        id_w = 5
        time_w = 8
        source_w = 10
        command_w = 18
        status_w = 6
        lines: list[tuple[str, str]] = []
        for ev in events:
            status = "OK" if ev.get("accepted") else "REJECT"
            source = self._source_label(str(ev.get("source") or ""))
            event_id = int(ev.get("id", 0) or 0)
            command = str(ev.get("command") or "")
            detail = self._localized_event_detail(ev)
            line = (
                f"{f'[{event_id:03d}]':<{id_w}} | {str(ev.get('time') or ''):<{time_w}} | "
                f"{source:<{source_w}} | {command:<{command_w}} | {status:<{status_w}} | {detail}"
            )
            lines.append((line, self._event_visual_color(command, bool(ev.get("accepted")))))
        return lines

    def _build_monitor_events_text(self, snapshot: dict) -> str:
        return "\n".join(line for line, _ in self._build_monitor_event_lines(snapshot))

    def _build_monitor_events_rich_text(self, snapshot: dict) -> str:
        id_w = 5
        time_w = 8
        source_w = 10
        command_w = 18
        status_w = 6
        current_generation = int(snapshot.get("event_generation", 0) or 0)
        rich_rows = []
        for ev in snapshot.get("events", []):
            event_id = int(ev.get("id", 0) or 0)
            event_label = f"[{event_id:03d}]"
            event_time = str(ev.get("time") or "")
            source = self._source_label(str(ev.get("source") or ""))
            status = "OK" if ev.get("accepted") else "REJECT"
            command = str(ev.get("command") or "")
            is_previous_session = int(ev.get("generation", 0) or 0) < current_generation
            color = "#6d8290" if is_previous_session else self._event_visual_color(command, bool(ev.get("accepted")))
            detail_lines = textwrap.wrap(
                self._localized_event_detail(ev), width=44,
                break_long_words=False, break_on_hyphens=False,
            ) or [""]
            prefix = (
                f"{event_label:<{id_w}} | {event_time:<{time_w}} | "
                f"{source:<{source_w}} | {command:<{command_w}} | {status:<{status_w}} | "
            )
            continuation = f"{'':<{id_w}} | {'':<{time_w}} | {'':<{source_w}} | {'':<{command_w}} | {'':<{status_w}} | "
            event_rows = [prefix + detail_lines[0]]
            event_rows.extend(continuation + line for line in detail_lines[1:])
            rich_rows.extend(
                f"<span style='color:{color};'>{html.escape(row)}</span>"
                for row in event_rows
            )
        return "<pre style='font-family:Consolas; font-size:12px;'>" + "\n".join(rich_rows) + "</pre>"

    def _localized_event_detail(self, event: dict) -> str:
        command = str(event.get("command") or "")
        original = str(event.get("detail") or "")
        if event.get("accepted"):
            if command == "SYSTEM_RESET":
                return self._tr("system_reset")
            if command == "SYSTEM_SHUTDOWN":
                return self._tr("system_shutdown")
            response = self._bridge.response_for_command(command, self._language)
            return response if response != command else original

        normalized = original.lower()
        if command == "UNKNOWN":
            return self._tr("invalid_unknown")
        if command == "NO_AUDIO":
            return self._tr("invalid_audio")
        if "sem alteracao" in normalized or "no change" in normalized:
            if command == "STOP":
                return self._tr("no_change_stop")
            if command.endswith("_OFF") or command.endswith("_RETRACT"):
                return self._tr("no_change_inactive", command=command)
            return self._tr("no_change_active", command=command)
        if "nao pode ainda" in normalized or "not allowed yet" in normalized:
            return self._tr("workflow_before_mode")
        if "modo de troca" in normalized or "mode change is active" in normalized:
            return self._tr("workflow_change_mode")
        if "nao pode mudar diretamente" in normalized or "direct mode switch" in normalized:
            return self._tr("workflow_direct_mode")
        if "neste modo nao pode" in normalized or "cannot control components" in normalized:
            return self._tr("workflow_components")
        if "no modo manual" in normalized or "in manual mode" in normalized:
            return self._tr("workflow_manual")
        return original

    def _source_label(self, source: str) -> str:
        if self._language == "en":
            labels = {
                "voice": "VOICE",
                "text": "TEXT-BOT",
                "mqtt_panel": "PHONE",
                "button": "BUTTON",
            }
        else:
            labels = {
                "voice": "VOZ",
                "text": "TEXT-BOT",
                "mqtt_panel": "TELEMOVEL",
                "button": "BOTAO",
            }
        return labels.get(source, source.upper())

    def _event_export_rows(self, events: list[dict]) -> list[dict[str, str]]:
        rows = []
        for ev in events:
            rows.append({
                "ID": f"{int(ev.get('id', 0) or 0):03d}",
                "Hora" if self._language == "pt" else "Time": str(ev.get("time") or ""),
                "Origem" if self._language == "pt" else "Source": self._source_label(str(ev.get("source") or "")),
                "Comando" if self._language == "pt" else "Command": str(ev.get("command") or ""),
                "Estado" if self._language == "pt" else "State": "OK" if ev.get("accepted") else "REJECT",
                "Descri\u00e7\u00e3o" if self._language == "pt" else "Description": self._localized_event_detail(ev),
            })
        return rows

    def _export_path(self, destination: str, prefix: str, fmt: str) -> str:
        selected = QUrl(destination).toLocalFile() if destination else ""
        extension = f".{fmt}"
        if selected and not os.path.splitext(selected)[1]:
            selected = os.path.join(selected, f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}{extension}")
        elif not selected:
            selected = os.path.join(os.getcwd(), "exports", f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}{extension}")
        elif not selected.lower().endswith(extension):
            selected += extension

        os.makedirs(os.path.dirname(os.path.abspath(selected)), exist_ok=True)
        return selected

    def _write_events_export(self, events: list[dict], fmt: str, destination: str) -> str:
        rows = self._event_export_rows(events)
        headers = list(rows[0].keys()) if rows else (
            ["ID", "Hora", "Origem", "Comando", "Estado", "Descri\u00e7\u00e3o"]
            if self._language == "pt"
            else ["ID", "Time", "Source", "Command", "State", "Description"]
        )

        if fmt == "pdf":
            path = self._export_path(destination, "blanky_eventos", "pdf")
            self._write_events_pdf(path, rows, headers)
            return path

        path = self._export_path(destination, "blanky_eventos", "csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _audio_diagnostic_rows(self) -> list[dict[str, str]]:
        if self._language == "pt":
            headers = ["ID", "Hora", "Captação", "Transcrição", "Comando", "Resultado", "Duração"]
        else:
            headers = ["ID", "Time", "Capture", "Transcript", "Command", "Result", "Duration"]

        rows = []
        for index, entry in enumerate(self._audio_diagnostic_entries, start=1):
            rows.append({
                headers[0]: f"{index:03d}",
                headers[1]: str(entry.get("time") or ""),
                headers[2]: f"{float(entry.get('capture') or 0.0):.2f} s",
                headers[3]: str(entry.get("text") or self._tr("no_audio")),
                headers[4]: str(entry.get("command") or "--"),
                headers[5]: str(entry.get("result") or "--"),
                headers[6]: f"{float(entry.get('duration') or 0.0):.2f} s",
            })
        return rows

    def _write_audio_diagnostics_export(self, fmt: str, destination: str) -> str:
        rows = self._audio_diagnostic_rows()
        headers = list(rows[0].keys()) if rows else (
            ["ID", "Hora", "Captação", "Transcrição", "Comando", "Resultado", "Duração"]
            if self._language == "pt"
            else ["ID", "Time", "Capture", "Transcript", "Command", "Result", "Duration"]
        )

        if fmt == "pdf":
            path = self._export_path(destination, "blanky_diagnostico_audio", "pdf")
            title = "Relatório de diagnóstico de áudio" if self._language == "pt" else "Audio diagnostic report"
            self._write_events_pdf(path, rows, headers, title)
            return path

        path = self._export_path(destination, "blanky_diagnostico_audio", "csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)
        return path

    @staticmethod
    def _pdf_text(value) -> bytes:
        """Encode a PDF text string with the characters used by Portuguese labels."""
        return (
            str(value).encode("cp1252", "replace")
            .replace(b"\\", b"\\\\")
            .replace(b"(", b"\\(")
            .replace(b")", b"\\)")
        )

    @staticmethod
    def _pdf_shorten(value, limit: int) -> str:
        text = str(value or "")
        return text if len(text) <= limit else text[: max(1, limit - 1)] + "…"

    def _write_events_pdf(
        self,
        path: str,
        rows: list[dict[str, str]],
        headers: list[str],
        report_title: str | None = None,
    ) -> None:
        """Create a self-contained, cross-platform PDF report without external tools."""
        page_width, page_height = 842, 595  # A4 landscape in PDF points.
        margin = 32
        audio_report = len(headers) == 7
        columns = [32, 68, 128, 190, 420, 538, 600] if audio_report else [32, 80, 148, 236, 390, 448]
        short_limits = [5, 8, 13, 20, 8]
        pages: list[bytes] = []

        def add_text(commands: list[bytes], x: float, y: float, value, *, size=9, bold=False, color=(0.1, 0.18, 0.25)):
            font = b"F2" if bold else b"F1"
            red, green, blue = color
            commands.append(
                f"BT /{font.decode()} {size} Tf {red:.3f} {green:.3f} {blue:.3f} rg "
                f"1 0 0 1 {x:.1f} {y:.1f} Tm (".encode("ascii")
                + self._pdf_text(value)
                + b") Tj ET\n"
            )

        def add_rule(commands: list[bytes], y: float, *, subtle: bool = False):
            color = "0.66 0.78 0.86" if subtle else "0.20 0.48 0.68"
            width = 0.25 if subtle else 0.45
            commands.append(
                f"{color} RG {width:.2f} w {margin} {y:.1f} m "
                f"{page_width - margin} {y:.1f} l S\n".encode("ascii")
            )

        def new_page(number: int) -> tuple[list[bytes], float]:
            commands: list[bytes] = []
            add_text(
                commands,
                margin,
                page_height - 35,
                report_title or self._tr("event_report_title"),
                size=16,
                bold=True,
                color=(0.03, 0.35, 0.58),
            )
            add_text(
                commands,
                margin,
                page_height - 50,
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                size=8,
                color=(0.28, 0.38, 0.46),
            )
            add_text(commands, page_width - 74, page_height - 50, f"{number}", size=8, color=(0.28, 0.38, 0.46))
            add_rule(commands, page_height - 58)
            for index, header in enumerate(headers):
                add_text(commands, columns[index], page_height - 73, header, size=8, bold=True, color=(0.03, 0.35, 0.58))
            add_rule(commands, page_height - 78)
            return commands, page_height - 92

        page_number = 1
        commands, y = new_page(page_number)
        for row in rows:
            values = [str(row.get(header, "")) for header in headers]
            if audio_report:
                wrapped_values = [
                    textwrap.wrap(value, width=limit, break_long_words=False, break_on_hyphens=False) or [""]
                    for value, limit in zip(values, [5, 8, 8, 28, 16, 8, 8])
                ]
                line_count = max(len(lines) for lines in wrapped_values)
                row_height = max(22, (line_count - 1) * 11 + 22)
                if y - row_height - 10 < margin + 18:
                    pages.append(b"".join(commands))
                    page_number += 1
                    commands, y = new_page(page_number)

                for index, lines in enumerate(wrapped_values):
                    for line_index, line in enumerate(lines):
                        add_text(commands, columns[index], y - line_index * 11, line, size=8)
                y -= row_height
                add_rule(commands, y + 3, subtle=True)
                y -= 10
                continue

            detail_lines = textwrap.wrap(values[-1], width=70, break_long_words=False, break_on_hyphens=False) or [""]
            row_height = max(22, (len(detail_lines) - 1) * 11 + 22)
            if y - row_height - 10 < margin + 18:
                pages.append(b"".join(commands))
                page_number += 1
                commands, y = new_page(page_number)

            for index in range(5):
                add_text(commands, columns[index], y, self._pdf_shorten(values[index], short_limits[index]), size=8)
            for line_index, line in enumerate(detail_lines):
                add_text(commands, columns[5], y - line_index * 11, line, size=8)
            y -= row_height
            add_rule(commands, y + 3, subtle=True)
            y -= 10

        pages.append(b"".join(commands))

        # A minimal PDF writer keeps the report portable and avoids GUI/application dependencies.
        objects: list[bytes] = [b"", b""]

        def add_object(data: bytes) -> int:
            objects.append(data)
            return len(objects)

        regular_font = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        bold_font = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        page_refs: list[int] = []
        for content in pages:
            content_ref = add_object(b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"endstream")
            page_refs.append(
                add_object(
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
                    f"/Resources << /Font << /F1 {regular_font} 0 R /F2 {bold_font} 0 R >> >> "
                    f"/Contents {content_ref} 0 R >>".encode("ascii")
                )
            )

        objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
        children = b" ".join(f"{ref} 0 R".encode("ascii") for ref in page_refs)
        objects[1] = b"<< /Type /Pages /Kids [" + children + b"] /Count " + str(len(page_refs)).encode("ascii") + b" >>"

        document = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(document))
            document.extend(f"{index} 0 obj\n".encode("ascii"))
            document.extend(obj)
            document.extend(b"\nendobj\n")
        xref_offset = len(document)
        document.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
        for offset in offsets[1:]:
            document.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        document.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
        )
        with open(path, "wb") as f:
            f.write(document)

    def _update_state_compact(self, state: dict):
        compact = "|".join(f"{key}={int(state.get(key, 0))}" for key in self._STATE_ORDER)
        if compact != self._state_compact:
            self._state_compact = compact
            self.stateCompactChanged.emit()

    def _refresh(self):
        self._set_datetime(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))

        snapshot = self._bridge.get_snapshot()
        health = self._bridge.health()
        mic = audio_info()
        health["microphone_ready"] = bool(mic.get("ready"))
        self._update_state_compact(snapshot.get("state", {}))

        self._set_comm(self._build_comm_line(health))
        self._set_comm_status_compact(self._build_comm_status_compact(health))
        self._set_comm_details_compact(self._build_comm_details_compact(health))
        self._set_monitor_left_text(self._build_monitor_left_text(snapshot, health))
        self._set_monitor_events_text(
            self._build_monitor_events_text(snapshot),
            self._build_monitor_events_rich_text(snapshot),
        )

        if not self._listening:
            for ev in self._wakeword.get_events():
                self._set_recognized("Palavra de ativação detetada." if self._language == "pt" else "Wake word detected.")
                self.startVoice()
                break

        events = snapshot.get("events", [])
        for ev in events:
            event_id = int(ev.get("id", 0))
            if event_id <= self._last_event_id_seen:
                continue
            self._last_event_id_seen = event_id

            if ev.get("source") == "mqtt_panel":
                self._stop_and_flush_audio()
                self._set_command_interaction("mqtt_status", str(ev.get("command") or ""))
                detail = self._localized_event_detail(ev)
                if detail:
                    self._enqueue_tts(detail)

    @Slot()
    def shutdown(self):
        try:
            self._wakeword.stop()
        except Exception:
            pass

