import json
import re
import threading
import time
from datetime import datetime
from typing import Any, Optional, Tuple

from blanky.config import (
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_CLIENT_ID,
    MQTT_ENABLED,
    MQTT_PASSWORD,
    MQTT_PULSE_SECONDS,
    MQTT_TOPIC_PREFIX,
    MQTT_USERNAME,
)
from blanky.mqtt_topics import (
    COMMAND_TO_TOPIC,
    command_for_topic_payload,
    command_outbound_payload,
    should_use_pulse,
)
from blanky.opcua_service import get_opcua_bridge


class MQTTBridge:
    def __init__(self):
        self.enabled = bool(MQTT_ENABLED)
        self._lock = threading.Lock()
        self._connected = False
        self._pulse_seconds = float(MQTT_PULSE_SECONDS)
        self._echo_suppression: dict[tuple[str, str], float] = {}
        self._events: list[dict[str, Any]] = []
        self._next_event_id = 1
        # Each reset starts a new visual event session without discarding history.
        self._event_generation = 0
        self._ui_lang = "pt"
        self._opcua = get_opcua_bridge()
        self._last_mqtt_panel_rx = 0.0

        self.state = {
            "start": 0,
            "mode_fast": 0,
            "mode_ideal": 0,
            "mode_manual": 0,
            "mode_change": 0,
            "motor_1": 0,
            "motor_2": 0,
            "motor_3": 0,
            "cyl_a": 0,
            "cyl_b": 0,
            "cyl_c": 0,
            "cyl_d": 0,
            "light_green": 0,
            "light_red": 0,
            "robot_metal": 0,
            "robot_nonmetal": 0,
        }

        self.client = None
        try:
            import paho.mqtt.client as mqtt
        except Exception:
            self.enabled = False
            return

        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID, clean_session=True)
        if MQTT_USERNAME:
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        if self.enabled:
            self._connect()

    def _on_connect(self, client, userdata, flags, rc):
        self._connected = (rc == 0)
        if self._connected:
            self._subscribe_command_topics()
            self.publish_all_state()

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

    def _on_message(self, client, userdata, msg):
        topic = str(msg.topic or "")
        payload = msg.payload.decode("utf-8", errors="ignore").strip()
        if self._is_suppressed_echo(topic, payload):
            return

        topic_suffix = self._extract_suffix(topic)
        if not topic_suffix:
            return

        command = command_for_topic_payload(topic_suffix, payload)
        if not command:
            return

        # Comando recebido do telemovel (IoT MQTT Panel) no mesmo topico usado pela voz.
        self._last_mqtt_panel_rx = time.monotonic()
        self.process_command(command=command, lang=self._ui_lang, source="mqtt_panel", emit_pulse=False)

    def _connect(self):
        try:
            self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 30)
            self.client.loop_start()
            self._connected = False
        except Exception:
            self.enabled = False
            self._connected = False

    def _topic(self, suffix: str) -> str:
        return f"{MQTT_TOPIC_PREFIX}/{suffix}"

    def _publish(self, topic_suffix: str, payload, retain: bool = True, suppress_echo: bool = False):
        if not self.enabled or self.client is None:
            return
        topic = self._topic(topic_suffix)
        payload_str = str(payload)
        if suppress_echo:
            self._echo_suppression[(topic, payload_str)] = time.monotonic() + 2.0
        self.client.publish(topic, payload_str, qos=1, retain=retain)

    def _subscribe_command_topics(self):
        if not self.enabled or self.client is None:
            return
        topics = set(COMMAND_TO_TOPIC.values())
        for suffix in topics:
            if suffix:
                self.client.subscribe(self._topic(suffix), qos=1)

    def _extract_suffix(self, full_topic: str) -> Optional[str]:
        prefix = f"{MQTT_TOPIC_PREFIX}/"
        if not full_topic.startswith(prefix):
            return None
        return full_topic[len(prefix):]

    def _is_suppressed_echo(self, full_topic: str, payload: str) -> bool:
        key = (full_topic, payload)
        expires = self._echo_suppression.get(key)
        if expires is None:
            return False
        now = time.monotonic()
        if now <= expires:
            return True
        del self._echo_suppression[key]
        return False

    def publish_all_state(self):
        for key, value in self.state.items():
            self._publish(f"state/{key}", value, retain=True)

    def process_command(
        self,
        command: str,
        lang: str,
        source: str = "voice",
        emit_pulse: Optional[bool] = None,
        bypass_workflow: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        with self._lock:
            self._publish(
                "events/last_command",
                json.dumps({"command": command, "source": source}, ensure_ascii=True),
                retain=True
            )

            if command in {"UNKNOWN", "NO_AUDIO"}:
                self._add_event(command=command, source=source, accepted=False, detail=self._workflow_message_invalid(command, lang))
                return False, None

            if not bypass_workflow:
                invalid_msg = self._workflow_message_invalid(command, lang)
                if invalid_msg:
                    self._publish_rejected(command, "workflow_blocked")
                    self._add_event(command=command, source=source, accepted=False, detail=invalid_msg)
                    return False, invalid_msg

            if command == "START":
                if self.state["start"] == 1:
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self.state["start"] = 1
                self._publish("state/start", 1, retain=True)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None

            if command == "STOP":
                if self._is_everything_reset():
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self._reset_all_state()
                self.publish_all_state()
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None

            if command == "MODE_FAST":
                if self.state["mode_fast"] == 1:
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self._set_modes(fast=1, ideal=0, manual=0, change=0)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None
            if command == "MODE_IDEAL":
                if self.state["mode_ideal"] == 1:
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self._set_modes(fast=0, ideal=1, manual=0, change=0)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None
            if command == "MODE_MANUAL":
                if self.state["mode_manual"] == 1:
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self._set_modes(fast=0, ideal=0, manual=1, change=0)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None
            if command == "MODE_UNSPEC":
                if self.state["mode_change"] == 1:
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self._set_modes(fast=0, ideal=0, manual=0, change=1)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None

            motor_match = re.match(r"^MOTOR_([123])_(ON|OFF)$", command)
            if motor_match:
                idx = motor_match.group(1)
                value = 1 if motor_match.group(2) == "ON" else 0
                key = f"motor_{idx}"
                if self.state[key] == value:
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self.state[key] = value
                self._publish(f"state/{key}", value, retain=True)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None

            cyl_match = re.match(r"^CYL_([ABCD])_(EXTEND|RETRACT)$", command)
            if cyl_match:
                letter = cyl_match.group(1).lower()
                value = 1 if cyl_match.group(2) == "EXTEND" else 0
                key = f"cyl_{letter}"
                if self.state[key] == value:
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self.state[key] = value
                self._publish(f"state/{key}", value, retain=True)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None

            if command == "GREEN_ON":
                if self.state["light_green"] == 1:
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self.state["light_green"] = 1
                self._publish("state/light_green", 1, retain=True)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None
            if command == "GREEN_OFF":
                if self.state["light_green"] == 0:
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self.state["light_green"] = 0
                self._publish("state/light_green", 0, retain=True)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None

            if command == "RED_ON":
                if self.state["light_red"] == 1:
                    msg = self._no_change_message(command, lang)
                    self._publish_rejected(command, "no_state_change")
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self.state["light_red"] = 1
                self._publish("state/light_red", 1, retain=True)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None
            if command == "RED_OFF":
                if self.state["light_red"] == 0:
                    msg = self._no_change_message(command, lang)
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self.state["light_red"] = 0
                self._publish("state/light_red", 0, retain=True)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None

            if command == "ROBOT_TO_METAL":
                if self.state["robot_metal"] == 1 and self.state["robot_nonmetal"] == 0:
                    msg = self._no_change_message(command, lang)
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self.state["robot_metal"] = 1
                self.state["robot_nonmetal"] = 0
                self._publish("state/robot_metal", 1, retain=True)
                self._publish("state/robot_nonmetal", 0, retain=True)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None

            if command == "ROBOT_TO_NONMETAL":
                if self.state["robot_metal"] == 0 and self.state["robot_nonmetal"] == 1:
                    msg = self._no_change_message(command, lang)
                    self._add_event(command=command, source=source, accepted=False, detail=msg)
                    return False, msg
                self._emit_for_command(command, emit_pulse)
                self.state["robot_metal"] = 0
                self.state["robot_nonmetal"] = 1
                self._publish("state/robot_metal", 0, retain=True)
                self._publish("state/robot_nonmetal", 1, retain=True)
                self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
                return True, None

            self._add_event(command=command, source=source, accepted=True, detail=self._response_for_command(command, lang))
            return True, None

    def _emit_command_pulse(self, command: str):
        outbound = command_outbound_payload(command)
        if not outbound:
            return
        suffix, on_payload = outbound

        self._publish(suffix, on_payload, retain=False, suppress_echo=True)

        timer = threading.Timer(
            self._pulse_seconds,
            lambda: self._publish(suffix, "0", retain=False, suppress_echo=True),
        )
        timer.daemon = True
        timer.start()

    def _emit_command_level(self, command: str):
        outbound = command_outbound_payload(command)
        if not outbound:
            return
        suffix, payload = outbound
        self._publish(suffix, payload, retain=False, suppress_echo=True)

    def _emit_for_command(self, command: str, emit_pulse: Optional[bool]):
        use_pulse = should_use_pulse(command) if emit_pulse is None else emit_pulse
        if use_pulse:
            self._emit_command_pulse(command)
        else:
            self._emit_command_level(command)

    def _publish_rejected(self, command: str, reason: str):
        self._publish(
            "events/rejected",
            json.dumps({"command": command, "reason": reason}, ensure_ascii=True),
            retain=False
        )

    def _set_modes(self, fast: int, ideal: int, manual: int, change: int):
        self.state["mode_fast"] = fast
        self.state["mode_ideal"] = ideal
        self.state["mode_manual"] = manual
        self.state["mode_change"] = change
        self._publish("state/mode_fast", fast, retain=True)
        self._publish("state/mode_ideal", ideal, retain=True)
        self._publish("state/mode_manual", manual, retain=True)
        self._publish("state/mode_change", change, retain=True)

    def _reset_all_state(self):
        for key in self.state.keys():
            self.state[key] = 0

    def _is_everything_reset(self) -> bool:
        return all(value == 0 for value in self.state.values())

    def _current_mode(self) -> str:
        if self.state["mode_fast"] == 1:
            return "fast"
        if self.state["mode_ideal"] == 1:
            return "ideal"
        if self.state["mode_manual"] == 1:
            return "manual"
        if self.state["mode_change"] == 1:
            return "change"
        return "none"

    def _is_component_command(self, command: str) -> bool:
        return (
            bool(re.match(r"^MOTOR_([123])_(ON|OFF)$", command))
            or bool(re.match(r"^CYL_([ABCD])_(EXTEND|RETRACT)$", command))
            or command in {"GREEN_ON", "GREEN_OFF", "RED_ON", "RED_OFF", "ROBOT_TO_METAL", "ROBOT_TO_NONMETAL"}
        )

    def _workflow_message_invalid(self, command: str, lang: str) -> Optional[str]:
        if command in {"UNKNOWN", "NO_AUDIO"}:
            return None

        if self.state["start"] == 0 and command not in {"START", "STOP"}:
            return (
                "Nao pode executar esse comando agora. Primeiro diga START."
                if lang == "pt"
                else "You cannot run that command now. Please set START first."
            )

        if command in {"START", "STOP"}:
            return None

        mode = self._current_mode()

        if mode == "none":
            if command in {"MODE_FAST", "MODE_IDEAL", "MODE_MANUAL"}:
                return None
            return (
                "Nao pode ainda. Depois de START deve escolher um modo: rapido, ideal ou manual. Pode tambem dizer STOP."
                if lang == "pt"
                else "Not allowed yet. After START, choose a mode: fast, ideal or manual. You can also say STOP."
            )

        if mode == "change":
            if command in {"MODE_FAST", "MODE_IDEAL", "MODE_MANUAL"}:
                return None
            return (
                "Modo de troca ativo. Escolha agora: rapido, ideal ou manual. Ou STOP."
                if lang == "pt"
                else "Mode change is active. Choose now: fast, ideal or manual. Or STOP."
            )

        if mode in {"fast", "ideal"}:
            if command == "MODE_UNSPEC":
                return None
            if command in {"MODE_FAST", "MODE_IDEAL", "MODE_MANUAL"}:
                if (mode == "fast" and command == "MODE_FAST") or (mode == "ideal" and command == "MODE_IDEAL"):
                    return None
                return (
                    "Nao pode mudar diretamente de modo. Use MODE_CHANGE e depois escolha o novo modo, ou diga STOP."
                    if lang == "pt"
                    else "Direct mode switch is not allowed. Use MODE_CHANGE and then select the new mode, or say STOP."
                )
            if self._is_component_command(command):
                return (
                    "Neste modo nao pode comandar componentes. Use MODE_CHANGE ou STOP."
                    if lang == "pt"
                    else "In this mode you cannot control components. Use MODE_CHANGE or STOP."
                )
            return None

        if mode == "manual":
            if command == "MODE_UNSPEC":
                return None
            if command in {"MODE_FAST", "MODE_IDEAL"}:
                return (
                    "No modo manual nao pode escolher rapido/ideal diretamente. Use MODE_CHANGE primeiro."
                    if lang == "pt"
                    else "In manual mode you cannot switch directly to fast/ideal. Use MODE_CHANGE first."
                )
            return None

        return None

    def _no_change_message(self, command: str, lang: str) -> str:
        if command == "STOP":
            return "Sem alteracao: sistema ja estava parado." if lang == "pt" else "No change: system was already stopped."
        if command.endswith("_OFF") or command.endswith("_RETRACT"):
            return (
                f"Sem alteracao: {command} ja estava desativado."
                if lang == "pt"
                else f"No change: {command} was already inactive."
            )
        return (
            f"Sem alteracao: {command} ja estava ativo."
            if lang == "pt"
            else f"No change: {command} was already active."
        )

    def _response_for_command(self, command: str, lang: str) -> str:
        pt = {
            "START": "Iniciado.",
            "STOP": "Parado.",
            "MODE_FAST": "Modo rapido ativado.",
            "MODE_IDEAL": "Modo ideal ativado.",
            "MODE_MANUAL": "Modo manual ativado.",
            "MODE_UNSPEC": "Modo alterado.",
            "GREEN_ON": "Luz verde acesa.",
            "GREEN_OFF": "Luz verde apagada.",
            "RED_ON": "Luz vermelha acesa.",
            "RED_OFF": "Luz vermelha apagada.",
            "ROBOT_TO_METAL": "Robo a ir para metal.",
            "ROBOT_TO_NONMETAL": "Robo a ir para nao metal.",
        }
        en = {
            "START": "Started.",
            "STOP": "Stopped.",
            "MODE_FAST": "Fast mode enabled.",
            "MODE_IDEAL": "Ideal mode enabled.",
            "MODE_MANUAL": "Manual mode enabled.",
            "MODE_UNSPEC": "Mode changed.",
            "GREEN_ON": "Green light on.",
            "GREEN_OFF": "Green light off.",
            "RED_ON": "Red light on.",
            "RED_OFF": "Red light off.",
            "ROBOT_TO_METAL": "Robot moving to metal.",
            "ROBOT_TO_NONMETAL": "Robot moving to non-metal.",
        }

        if command.startswith("MOTOR_"):
            parts = command.split("_")
            motor = parts[1]
            state = parts[2]
            if lang == "pt":
                return f"Motor {motor} ativado." if state == "ON" else f"Motor {motor} desativado."
            return f"Motor {motor} activated." if state == "ON" else f"Motor {motor} deactivated."

        if command.startswith("CYL_"):
            parts = command.split("_")
            letter = parts[1]
            state = parts[2]
            if lang == "pt":
                return f"Cilindro {letter} a avancar." if state == "EXTEND" else f"Cilindro {letter} a recuar."
            return f"Cylinder {letter} extending." if state == "EXTEND" else f"Cylinder {letter} retracting."

        mapping = pt if lang == "pt" else en
        return mapping.get(command, command)

    def _add_event(self, command: str, source: str, accepted: bool, detail: Optional[str]):
        event = {
            "id": self._next_event_id,
            "time": datetime.now().strftime("%H:%M:%S"),
            "source": source,
            "command": command,
            "accepted": accepted,
            "detail": detail or "",
            "generation": self._event_generation,
        }
        self._next_event_id += 1
        self._events.append(event)

        if accepted:
            self._opcua.enqueue_command(command)

    def reset_system(self, lang: str, source: str = "button") -> Tuple[bool, str]:
        with self._lock:
            self._reset_all_state()
            self.publish_all_state()
            # Preserve all existing events, but make subsequent events part of a new session.
            self._event_generation += 1
            msg = (
                "Sistema reinicializado. Todas as variaveis foram repostas a zero."
                if lang == "pt"
                else "System reset. All variables were restored to zero."
            )
            self._add_event(command="SYSTEM_RESET", source=source, accepted=True, detail=msg)
            return True, msg

    def shutdown_system(self, lang: str, source: str = "button") -> Tuple[bool, str]:
        with self._lock:
            self._reset_all_state()
            self.publish_all_state()
            msg = "Sistema a desligar." if lang == "pt" else "System shutting down."
            self._add_event(command="SYSTEM_SHUTDOWN", source=source, accepted=True, detail=msg)
            return True, msg

    def response_for_command(self, command: str, lang: str) -> str:
        return self._response_for_command(command, lang)

    def get_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "state": dict(self.state),
                "events": list(self._events),
                "event_generation": self._event_generation,
            }

    def health(self) -> dict[str, Any]:
        now = time.monotonic()
        mqtt_panel_active = (now - self._last_mqtt_panel_rx) <= 30.0
        mqtt_panel_last_rx_seconds = (
            max(0.0, now - self._last_mqtt_panel_rx) if self._last_mqtt_panel_rx else None
        )
        opcua_health = self._opcua.health()
        return {
            "mqtt_base_connected": bool(self.enabled and self._connected),
            "mqtt_panel_active": mqtt_panel_active,
            "mqtt_panel_last_rx_seconds": mqtt_panel_last_rx_seconds,
            "opcua_connected": bool(opcua_health.get("connected")),
            "opcua_last_error": str(opcua_health.get("last_error") or ""),
            "opcua_last_write": str(opcua_health.get("last_write") or ""),
        }

    def set_ui_lang(self, lang: str):
        with self._lock:
            self._ui_lang = "pt" if lang not in {"pt", "en"} else lang


_BRIDGE: Optional[MQTTBridge] = None


def get_mqtt_bridge() -> MQTTBridge:
    global _BRIDGE
    if _BRIDGE is None:
        _BRIDGE = MQTTBridge()
    return _BRIDGE
