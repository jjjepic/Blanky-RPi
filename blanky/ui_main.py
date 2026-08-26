import os
import queue
import sys
import threading
from datetime import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from blanky.audio_service import audio_info, play_wav
from blanky.config import AUDIO_DIR
from blanky.mqtt_service import get_mqtt_bridge
from blanky.speech_service import tts_speak_to_wav
from blanky.voice_worker import VoiceWorker


ICON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "assets", "blanky_logo_dark.png")
)


class MonitorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blanky - Monitor MQTT/OPCUA")
        self.resize(760, 520)
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.setStyleSheet("QWidget {background-color: #070b12; color: #d9efff;}")
        self.txt = QTextEdit(self)
        self.txt.setReadOnly(True)
        self.txt.setGeometry(10, 10, 740, 500)
        self.txt.setStyleSheet(
            "QTextEdit {"
            "background-color: #071a2a;"
            "color: #9dd9ff;"
            "border: 1px solid #1d5274;"
            "font-family: Consolas, 'DejaVu Sans Mono', monospace;"
            "font-size: 12px;"
            "}"
        )

    def update_snapshot(self, snapshot: dict, health: dict):
        state = snapshot.get("state", {})
        events = snapshot.get("events", [])[-80:]
        bar = self.txt.verticalScrollBar()
        was_at_bottom = bar.value() >= (bar.maximum() - 2)
        previous_value = bar.value()

        lines = ["== COMUNICACOES ==", ""]
        lines.append(f"Microfone: {'OK' if health.get('microphone_ready') else 'OFF'}")
        lines.append(f"MQTT Base: {'OK' if health.get('mqtt_base_connected') else 'OFF'}")
        lines.append(f"MQTT Telemovel: {'OK' if health.get('mqtt_panel_active') else 'SEM TRAFEGO RECENTE'}")
        lines.append(f"OPCUA: {'OK' if health.get('opcua_connected') else 'OFF'}")
        if health.get("opcua_last_write"):
            lines.append(f"Ultima escrita OPCUA: {health.get('opcua_last_write')}")
        if health.get("opcua_last_error"):
            lines.append(f"Erro OPCUA: {health.get('opcua_last_error')}")

        lines.append("")
        lines.append("== ESTADO ==")
        lines.append("")
        for key in sorted(state.keys()):
            lines.append(f"{key}: {state[key]}")

        lines.append("")
        lines.append("== EVENTOS (ultimos) ==")
        lines.append("")
        for ev in events:
            status = "OK" if ev.get("accepted") else "REJECT"
            lines.append(
                f"[{ev.get('id')}] {ev.get('time')} | {ev.get('source')} | {ev.get('command')} | {status} | {ev.get('detail')}"
            )

        self.txt.setPlainText("\n".join(lines))
        if was_at_bottom:
            bar.setValue(bar.maximum())
        else:
            bar.setValue(previous_value)


class BlankyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blanky11")
        self.resize(860, 560)
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.lang = "pt"
        self.worker = None
        self.bridge = get_mqtt_bridge()
        self.bridge.set_ui_lang(self.lang)
        self.last_event_id_seen = 0
        self.monitor = MonitorWindow()

        self._tts_queue: queue.Queue[str] = queue.Queue()
        self._panel_tts_path = os.path.join(AUDIO_DIR, "tts_panel.wav")
        self._tts_thread = threading.Thread(target=self._panel_tts_loop, daemon=True)
        self._tts_thread.start()

        self.dark_mode = True
        self._build_ui()
        self.apply_theme()
        self.update_lang_ui()

        self.monitor_timer = QTimer(self)
        self.monitor_timer.setInterval(500)
        self.monitor_timer.timeout.connect(self.refresh_data)
        self.monitor_timer.start()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(12)

        top_row = QHBoxLayout()
        self.btn_theme = QPushButton("\u263D Dark", self)
        self.btn_theme.setCheckable(True)
        self.btn_theme.setChecked(True)
        self.btn_theme.setMaximumWidth(120)
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.lbl_datetime = QLabel("--", self)
        self.lbl_datetime.setObjectName("datetime")
        self.lbl_datetime.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top_row.addWidget(self.btn_theme, 0, Qt.AlignLeft)
        top_row.addStretch(1)
        top_row.addWidget(self.lbl_datetime, 0, Qt.AlignRight)
        root.addLayout(top_row)

        title = QLabel("Blanky Industrial Control", self)
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        self.lbl_comm = QLabel("Comunicacoes: --", self)
        self.lbl_comm.setObjectName("comm")
        self.lbl_comm.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_comm)

        display = QFrame(self)
        display.setObjectName("display")
        display_layout = QVBoxLayout(display)
        display_layout.setContentsMargins(18, 14, 18, 14)
        display_layout.setSpacing(10)

        self.lbl_status = QLabel("Estado: Idle (PT)", self)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setObjectName("status")

        self.lbl_title = QLabel("Texto reconhecido:", self)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setObjectName("subtitle")

        self.lbl_text = QLabel("---", self)
        self.lbl_text.setAlignment(Qt.AlignCenter)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setObjectName("recognized")

        display_layout.addWidget(self.lbl_status)
        display_layout.addWidget(self.lbl_title)
        display_layout.addWidget(self.lbl_text)
        root.addWidget(display)

        self.btn_listen = QPushButton("OUVIR COMANDO", self)
        self.btn_listen.setObjectName("primary")
        self.btn_listen.setFixedHeight(42)
        self.btn_listen.clicked.connect(self.start_voice_flow)

        self.btn_monitor = QPushButton("ABRIR MONITOR MQTT / OPCUA", self)
        self.btn_monitor.setFixedHeight(42)
        self.btn_monitor.clicked.connect(self.open_monitor)

        commands_row = QHBoxLayout()
        commands_row.addWidget(self.btn_listen)
        commands_row.addWidget(self.btn_monitor)
        root.addLayout(commands_row)

        lang_row = QHBoxLayout()
        self.btn_pt = QPushButton("PT (Portugues)", self)
        self.btn_pt.setFixedHeight(38)
        self.btn_pt.clicked.connect(lambda: self.set_lang("pt"))

        self.btn_en = QPushButton("EN (Ingles)", self)
        self.btn_en.setFixedHeight(38)
        self.btn_en.clicked.connect(lambda: self.set_lang("en"))

        lang_row.addWidget(self.btn_pt)
        lang_row.addWidget(self.btn_en)
        root.addLayout(lang_row)

    def apply_theme(self):
        dark_style = (
            "QWidget {"
            "background-color: #02060d;"
            "color: #def2ff;"
            "font-family: 'Segoe UI', 'Noto Sans', sans-serif;"
            "}"
            "QLabel#title {font-size: 24px; font-weight: 800; color: #63cbff; letter-spacing: 1px;}"
            "QLabel#datetime {font-size: 12px; color: #b5d9ef; padding: 4px 8px; background-color: #0b1824; border: 1px solid #1f4f70; border-radius: 8px;}"
            "QLabel#comm {font-size: 13px; color: #b7dfff; padding: 6px; background-color: #091722; border: 1px solid #1e5f89; border-radius: 10px;}"
            "QFrame#display {background-color: #050d17; border: 2px solid #1f6fa8; border-radius: 14px;}"
            "QLabel#status {font-size: 18px; font-weight: 700; color: #9fe1ff;}"
            "QLabel#subtitle {font-size: 13px; color: #83c6ec;}"
            "QLabel#recognized {background-color: #081a2b; border: 1px solid #2b83bf; border-radius: 10px; padding: 14px; font-size: 17px; font-weight: 600; color: #e0f5ff;}"
            "QPushButton {background-color: #0d2942; border: 1px solid #2c89c7; color: #eaf7ff; padding: 8px; border-radius: 10px; font-size: 13px; font-weight: 650;}"
            "QPushButton:hover {background-color: #124364;}"
            "QPushButton:pressed {background-color: #1b5f8a;}"
            "QPushButton#primary {background-color: #0a3a57; border: 2px solid #3ab8ff; font-size: 14px;}"
            "QPushButton:disabled {background-color: #1a2129; color: #7e8c99; border-color: #2b3a47;}"
        )
        light_style = (
            "QWidget {background-color: #edf5fb; color: #12364f; font-family: 'Segoe UI', 'Noto Sans', sans-serif;}"
            "QLabel#title {font-size: 24px; font-weight: 800; color: #0a5e8f;}"
            "QLabel#datetime {font-size: 12px; color: #10405f; padding: 4px 8px; background-color: #d8eaf5; border: 1px solid #86b4cf; border-radius: 8px;}"
            "QLabel#comm {font-size: 13px; color: #11486b; padding: 6px; background-color: #d9ecf8; border: 1px solid #7aacc9; border-radius: 10px;}"
            "QFrame#display {background-color: #f7fbff; border: 2px solid #70acd1; border-radius: 14px;}"
            "QLabel#status {font-size: 18px; font-weight: 700; color: #0f5882;}"
            "QLabel#subtitle {font-size: 13px; color: #2e6d92;}"
            "QLabel#recognized {background-color: #eaf5fd; border: 1px solid #76b2d8; border-radius: 10px; padding: 14px; font-size: 17px; font-weight: 600; color: #093d5e;}"
            "QPushButton {background-color: #d3e9f8; border: 1px solid #6da5c7; color: #0b4060; padding: 8px; border-radius: 10px; font-size: 13px; font-weight: 650;}"
            "QPushButton:hover {background-color: #c2e2f5;}"
            "QPushButton:pressed {background-color: #afd6ef;}"
            "QPushButton#primary {background-color: #bce2fb; border: 2px solid #5ba8d8; font-size: 14px;}"
            "QPushButton:disabled {background-color: #e2e7ec; color: #7d8a95; border-color: #bcc8d2;}"
        )
        self.setStyleSheet(dark_style if self.dark_mode else light_style)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.btn_theme.setText("\u263D Dark" if self.dark_mode else "\u2600 Light")
        self.apply_theme()
        self.update_lang_ui()

    def _panel_tts_loop(self):
        while True:
            text = self._tts_queue.get()
            if not text:
                continue
            try:
                tts_speak_to_wav(text, self._panel_tts_path)
                play_wav(self._panel_tts_path)
            except Exception:
                pass

    def set_lang(self, lang: str):
        self.lang = lang
        self.bridge.set_ui_lang(lang)
        self.update_lang_ui()

    def update_lang_ui(self):
        normal = ""
        active = "font-weight:700; border:2px solid #29b2ff; background-color:#114a70;"
        self.btn_pt.setStyleSheet(active if self.lang == "pt" else normal)
        self.btn_en.setStyleSheet(active if self.lang == "en" else normal)

        if self.lang == "pt":
            self.lbl_status.setText("Estado: Idle (PT)")
        else:
            self.lbl_status.setText("Status: Idle (EN)")

    def start_voice_flow(self):
        self.btn_listen.setEnabled(False)
        self.lbl_text.setText("---")
        self.lbl_status.setText("Estado: A iniciar..." if self.lang == "pt" else "Status: Starting...")

        self.worker = VoiceWorker(lang=self.lang)
        self.worker.status.connect(self.lbl_status.setText)
        self.worker.recognized.connect(self.on_recognized)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def on_recognized(self, text: str):
        if not text:
            self.lbl_text.setText("(sem audio detetado)" if self.lang == "pt" else "(no audio detected)")
        else:
            self.lbl_text.setText(text)

    def on_done(self):
        self.btn_listen.setEnabled(True)
        self.worker = None
        self.update_lang_ui()

    def open_monitor(self):
        self.monitor.show()
        self.monitor.raise_()
        self.monitor.activateWindow()

    def _build_comm_line(self, health: dict) -> str:
        parts = [
            f"Microfone={'OK' if health.get('microphone_ready') else 'OFF'}",
            f"MQTT Base={'OK' if health.get('mqtt_base_connected') else 'OFF'}",
            f"MQTT Telemovel={'OK' if health.get('mqtt_panel_active') else 'SEM TRAFEGO'}",
            f"OPCUA={'OK' if health.get('opcua_connected') else 'OFF'}",
        ]
        if health.get("opcua_last_error"):
            parts.append(f"Erro OPCUA={health.get('opcua_last_error')}")
        return " | ".join(parts)

    def refresh_data(self):
        snapshot = self.bridge.get_snapshot()
        health = self.bridge.health()
        mic = audio_info()
        health["microphone_ready"] = bool(mic.get("ready"))
        self.lbl_datetime.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))

        self.lbl_comm.setText(self._build_comm_line(health))
        self.monitor.update_snapshot(snapshot, health)

        events = snapshot.get("events", [])
        for ev in events:
            event_id = int(ev.get("id", 0))
            if event_id <= self.last_event_id_seen:
                continue
            self.last_event_id_seen = event_id

            if ev.get("source") == "mqtt_panel":
                self.lbl_text.setText(f"[MQTT] {ev.get('command')}")
                detail = str(ev.get("detail") or "")
                if detail:
                    self._tts_queue.put(detail)


def run_app():
    app = QApplication(sys.argv)
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    w = BlankyWindow()
    w.show()
    sys.exit(app.exec())
