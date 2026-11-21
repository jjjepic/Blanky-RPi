import json
import os
import re
import threading
import time
from datetime import datetime
from typing import Any, Callable, Optional, Tuple

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
from blanky.opcua_nodes import COMMAND_TO_NODE
from blanky.plc_state import STATE_KEYS, command_target, project_plc_state
from blanky.command_messages import (command_label, no_change_message, plc_change_message,
                                      plc_observation_message, rejection_for_event, rejection_message)
from blanky.mqtt_monitor import health_monitor_updates, state_monitor_updates
from blanky.command_parser import VALID_COMMANDS, VALID_COMPONENTS, VALID_GROUPS, VALID_QUERIES
from blanky.openai_activity import activity_snapshot
from blanky.status_queries import answer_query_parts


_TEST_PULSE_SECONDS = 2.0
_TEST_PULSE_COMMANDS = frozenset({
    "CYL_C_EXTEND", "CYL_D_EXTEND", "ROBOT_TO_METAL", "ROBOT_TO_NONMETAL",
})


class MQTTBridge:
    _PHONE_TEXT_TOPICS = {"textbot/online": "online", "textbot/offline": "offline"}
    _MAX_PHONE_TEXT_LENGTH = 1000
    _MONITOR_SYNC_TOPIC = "monitor/sync"
    _MONITOR_SYNC_INTERVAL = 2.0

    def __init__(self):
        self.enabled = bool(MQTT_ENABLED)
        self._lock = threading.Lock()
        self._connected = False
        self._broker_host = str(MQTT_BROKER_HOST)
        self._broker_port = int(MQTT_BROKER_PORT)
        self._topic_prefix = str(MQTT_TOPIC_PREFIX)
        self._username = MQTT_USERNAME
        self._password = MQTT_PASSWORD
        self._client_id = str(MQTT_CLIENT_ID)
        self._pulse_seconds = float(MQTT_PULSE_SECONDS)
        self._echo_suppression: dict[tuple[str, str], float] = {}
        self._events: list[dict[str, Any]] = []
        self._last_interaction_response = {"pt": "", "en": ""}
        self._next_event_id = 1
        # Each reset starts a new visual event session without discarding history.
        self._event_generation = 0
        self._ui_lang = "pt"
        self._opcua = get_opcua_bridge()
        self._last_mqtt_panel_rx = 0.0
        self._last_monitor_sync = float("-inf")
        self._monitor_health_cache: dict[str, str] = {}
        self._mobile_text_handler: Optional[Callable[[str, str], None]] = None

        self.state = {key: None for key in STATE_KEYS}
        self.state_quality = {key: "unavailable" for key in STATE_KEYS}
        self._plc_available = False
        self._plc_epoch = None
        self._last_known: dict[str, int] = {}
        self._pending_commands: dict[str, dict] = {}
        self._plc_received: dict[str, bool] = {}
        self._plc_error_latched = False
        self._last_valid_read = ""
        # Never persist test mode: a fresh process always trusts PLC feedback.
        self._control_mode = "plc"
        self._test_pulses: dict[str, tuple[threading.Timer, str]] = {}

        self.client = None
        try:
            import paho.mqtt.client as mqtt
        except Exception:
            self.enabled = False
            return

        self._mqtt = mqtt
        self.client = self._create_client()

        if self.enabled:
            self._connect()

    def _create_client(self):
        client = self._mqtt.Client(client_id=self._client_id, clean_session=True)
        client.will_set(self._topic("monitor/availability"), payload="offline", qos=1, retain=True)
        if self._username:
            client.username_pw_set(self._username, self._password)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        return client

    def configure_connection(self, host: str, port: int, topic_prefix: str):
        """Reconnect MQTT using editable, locally stored endpoint settings."""
        host = (host or MQTT_BROKER_HOST).strip()
        topic_prefix = (topic_prefix or MQTT_TOPIC_PREFIX).strip().strip("/")
        try:
            port = int(port)
        except (TypeError, ValueError):
            port = MQTT_BROKER_PORT
        port = max(1, min(port, 65535))

        # Keep the editable values available even on installations without paho-mqtt.
        if not hasattr(self, "_mqtt"):
            self._broker_host = host
            self._broker_port = port
            self._topic_prefix = topic_prefix
            return

        if (
            host == self._broker_host
            and port == self._broker_port
            and topic_prefix == self._topic_prefix
        ):
            return

        previous_client = self.client
        if previous_client is not None:
            self._publish_offline(previous_client)
            self._connected = False
            try:
                previous_client.disconnect()
            except Exception:
                pass
            try:
                previous_client.loop_stop()
            except Exception:
                pass

        self._broker_host = host
        self._broker_port = port
        self._topic_prefix = topic_prefix
        self.enabled = bool(MQTT_ENABLED)
        self.client = self._create_client()
        if self.enabled:
            self._connect()

    def configure_opcua_connection(self, url: str):
        self._opcua.configure_connection(url)

    def _on_connect(self, client, userdata, flags, rc):
        self._connected = (rc == 0)
        if self._connected:
            self._monitor_health_cache = {}
            self._last_monitor_sync = float("-inf")
            self._subscribe_command_topics()
            self.publish_all_state()
            self._publish("monitor/availability", "online")
            if self._events:
                self._publish_monitor_event(self._events[-1])
            else:
                self._publish("monitor/pt/last_message", "Sem atividade.")
                self._publish("monitor/en/last_message", "No activity yet.")
                self._publish("monitor/last_event_status", "none")
                self._publish("monitor/last_event_stage", "none")
            phone_events = (event for event in reversed(self._events) if event["source"] == "mqtt_text")
            last_phone_event = next(phone_events, None)
            if last_phone_event is None:
                self._publish_phone_text_response("Sem pedidos.", "No requests yet.")
                self._publish("monitor/pt/phone_textbot_path", "Sem pedidos")
                self._publish("monitor/en/phone_textbot_path", "No requests yet")
            else:
                self._publish_phone_event(last_phone_event)
            self.publish_monitor_health(self.health())

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

    def _on_message(self, client, userdata, msg):
        if getattr(msg, "retain", False):
            return
        topic = str(msg.topic or "")
        topic_suffix = self._extract_suffix(topic)
        if not topic_suffix:
            return

        if topic_suffix == self._MONITOR_SYNC_TOPIC:
            if msg.payload == b"sync":
                now = time.monotonic()
                self._last_mqtt_panel_rx = now
                if now - self._last_monitor_sync >= self._MONITOR_SYNC_INTERVAL:
                    self._last_monitor_sync = now
                    self.publish_all_state()
                    self.publish_monitor_health(self.health(), force=True)
                    self._publish("monitor/availability", "online")
            return

        mode = self._PHONE_TEXT_TOPICS.get(topic_suffix)
        if mode:
            if getattr(msg, "retain", False):
                return
            self._last_mqtt_panel_rx = time.monotonic()
            try:
                payload = msg.payload.decode("utf-8").strip() if len(msg.payload) <= 4000 else ""
            except UnicodeDecodeError:
                payload = ""
            if not payload or len(payload) > self._MAX_PHONE_TEXT_LENGTH:
                self._publish_phone_text_response(
                    "Escreve um pedido até 1000 caracteres.",
                    "Enter a request of up to 1000 characters.",
                )
                return
            if self._mobile_text_handler is None:
                self._publish_phone_text_response(
                    "Text-Bot indisponível. Tenta novamente.",
                    "Text-Bot unavailable. Please try again.",
                )
                return
            self._publish_phone_text_response("A interpretar...", "Interpreting...")
            try:
                self._mobile_text_handler(payload, mode)
            except Exception:
                self._publish_phone_text_response(
                    "Text-Bot indisponível. Tenta novamente.",
                    "Text-Bot unavailable. Please try again.",
                )
            return

        payload = msg.payload.decode("utf-8", errors="ignore").strip()
        if self._is_suppressed_echo(topic, payload):
            return
        command = command_for_topic_payload(topic_suffix, payload)
        if not command:
            return

        # Comando recebido do telemovel (IoT MQTT Panel) no mesmo topico usado pela voz.
        self._last_mqtt_panel_rx = time.monotonic()
        self.process_command(command=command, lang=self._ui_lang, source="mqtt_panel", emit_pulse=False)

    def _connect(self):
        self._connected = False
        try:
            self.client.connect(self._broker_host, self._broker_port, 30)
            self.client.loop_start()
        except Exception:
            self.enabled = False
            self._connected = False

    def _topic(self, suffix: str) -> str:
        return f"{self._topic_prefix}/{suffix}"

    def _publish(self, topic_suffix: str, payload, retain: bool = True, suppress_echo: bool = False):
        if not self.enabled or self.client is None:
            return
        topic = self._topic(topic_suffix)
        payload_str = str(payload)
        if suppress_echo:
            self._echo_suppression[(topic, payload_str)] = time.monotonic() + 2.0
        self.client.publish(topic, payload_str, qos=1, retain=retain)
        if topic_suffix.startswith("state/"):
            key = topic_suffix.removeprefix("state/")
            for monitor_suffix, monitor_payload in state_monitor_updates(
                self.state, key, local=self.state_quality.get(key) == "local"
            ).items():
                self._publish(monitor_suffix, monitor_payload)

    def _publish_offline(self, client):
        if not self._connected:
            return
        try:
            info = client.publish(self._topic("monitor/availability"), "offline", qos=1, retain=True)
            info.wait_for_publish(timeout=1.0)
        except Exception:
            pass

    def close(self):
        """Mark a clean exit offline; the broker's Will covers unexpected exits."""
        with self._lock:
            self._cancel_test_pulses()
        client = self.client
        if client is None:
            return
        self._publish_offline(client)
        self._connected = False
        try:
            client.disconnect()
        except Exception:
            pass
        try:
            client.loop_stop()
        except Exception:
            pass

    def publish_monitor_health(self, health: dict, *, force: bool = False):
        if not self.enabled or not self._connected:
            return
        for suffix, payload in health_monitor_updates(health).items():
            if force or self._monitor_health_cache.get(suffix) != payload:
                self._publish(suffix, payload)
                self._monitor_health_cache[suffix] = payload

    def _subscribe_command_topics(self):
        if not self.enabled or self.client is None:
            return
        topics = set(COMMAND_TO_TOPIC.values())
        for suffix in topics:
            if suffix:
                self.client.subscribe(self._topic(suffix), qos=1)
        for suffix in self._PHONE_TEXT_TOPICS:
            self.client.subscribe(self._topic(suffix), qos=0)
        self.client.subscribe(self._topic(self._MONITOR_SYNC_TOPIC), qos=1)

    def set_mobile_text_handler(self, handler: Optional[Callable[[str, str], None]]):
        self._mobile_text_handler = handler

    def _publish_phone_text_response(self, pt: str, en: str):
        self._publish("monitor/pt/phone_textbot_response", pt)
        self._publish("monitor/en/phone_textbot_response", en)

    def publish_phone_interaction_response(self, pt: str, en: str):
        self._publish_phone_text_response(pt, en)

    def publish_phone_text_path(self, mode: str, fallback: bool = False):
        if fallback:
            pt, en = "Online indisponível; usado Offline", "Online unavailable; used Offline"
        elif mode == "online":
            pt, en = "Online", "Online"
        else:
            pt, en = "Offline", "Offline"
        self._publish("monitor/pt/phone_textbot_path", pt)
        self._publish("monitor/en/phone_textbot_path", en)

    def _extract_suffix(self, full_topic: str) -> Optional[str]:
        prefix = f"{self._topic_prefix}/"
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
        self._synchronize_plc()
        with self._lock:
            self._publish_control_mode()
            for key, value in self.state.items():
                self._publish(f"state/{key}", value if value is not None else "unknown", retain=True)
                self._publish(f"state_quality/{key}", self.state_quality[key], retain=True)

    def _synchronize_plc(self):
        health = self._opcua.health() if hasattr(self._opcua, "health") else {}
        records = self._opcua.timing_records() if hasattr(self._opcua, "timing_records") else []
        available = bool(health.get("connected") and health.get("feedback_active"))
        received = dict(health.get("received") or {})
        state, quality = project_plc_state(received, available)
        alarm_known = state["system_error"] is not None
        epoch = health.get("feedback_epoch")
        with self._lock:
            if self._control_mode == "test":
                self._plc_available = available
                self._plc_received = received if available else {}
                self._last_valid_read = str(health.get("last_valid_read") or "")
                # A real PLC alarm must remain visible even while other states are local.
                if alarm_known:
                    self._plc_error_latched = bool(received.get("system_error"))
                alarm = self._plc_error_latched
                alarm_value = int(alarm)
                alarm_quality = "confirmed" if alarm_known and alarm else "unavailable" if alarm else "local"
                if self.state["system_error"] != alarm_value or self.state_quality["system_error"] != alarm_quality:
                    self.state["system_error"] = alarm_value
                    self.state_quality["system_error"] = alarm_quality
                    self._publish("state/system_error", alarm_value, retain=True)
                    self._publish("state_quality/system_error", alarm_quality, retain=True)
                    if alarm:
                        self._add_event("PLC_STATE", "plc", True,
                                        plc_change_message("system_error", 1, self._ui_lang),
                                        reason="system_error",
                                        detail_pt=plc_change_message("system_error", 1, "pt"),
                                        detail_en=plc_change_message("system_error", 1, "en"))
                return
            new_baseline = epoch != self._plc_epoch or (available and not self._plc_available)
            self._plc_epoch = epoch
            self._plc_available = available
            self._plc_received = received if available else {}
            if alarm_known:
                self._plc_error_latched = bool(received.get("system_error"))
            self._last_valid_read = str(health.get("last_valid_read") or "")
            if new_baseline or not available:
                self._last_known = {key: value for key, value in state.items() if value is not None}
            by_id = {record.get("id"): record for record in records}
            for key, value in state.items():
                previous = self.state[key]
                previous_quality = self.state_quality[key]
                self.state[key] = value
                self.state_quality[key] = quality[key]
                if previous != value or previous_quality != quality[key]:
                    self._publish(f"state/{key}", value if value is not None else "unknown", retain=True)
                    self._publish(f"state_quality/{key}", quality[key], retain=True)
                if available and not new_baseline and value is not None:
                    before = self._last_known.get(key)
                    if before != value:
                        pending = self._pending_commands.get(key, {})
                        record_id = pending.get("record_id")
                        matching_return = (pending.get("target") == value and quality[key] == "confirmed"
                                           and by_id.get(record_id, {}).get("ack_status") == "state_observed")
                        self._add_event("PLC_STATE", "plc", True, plc_change_message(key, value, self._ui_lang),
                                        detail_pt=plc_change_message(key, value, "pt"),
                                        detail_en=plc_change_message(key, value, "en"),
                                        plc_key=key, plc_value=value,
                                        request_pending=key in self._pending_commands,
                                        request_id=record_id if matching_return else None,
                                        reason="system_error" if key == "system_error" and value else "state_change")
                    self._last_known[key] = value

            for key, pending in list(self._pending_commands.items()):
                record = by_id.get(pending["record_id"])
                status = record.get("ack_status") if record else "queued"
                if time.monotonic() - pending["created_at"] >= 6.0 and status in {"queued", "pending", "state_observed"}:
                    status = "timeout"
                if record and record.get("write_ms") is not None and pending["stage"] == "queued":
                    pending["stage"] = "written"
                    self._add_event(pending["command"], "opcua", True,
                                    "Escrita OPC UA concluída; a aguardar o estado do PLC."
                                    if self._ui_lang == "pt" else "OPC UA write completed; awaiting PLC state.",
                                    reason="written", detail_pt="Escrita OPC UA concluída; a aguardar o estado do PLC.",
                                    detail_en="OPC UA write completed; awaiting PLC state.", request_id=pending["record_id"])
                if (status == "state_observed" and pending["stage"] == "written"
                        and state[key] == pending["target"] and quality[key] == "confirmed"):
                    self._add_event(pending["command"], "plc", True,
                                    plc_observation_message(pending["command"], self._ui_lang),
                                    reason="state_observed",
                                    detail_pt=plc_observation_message(pending["command"], "pt"),
                                    detail_en=plc_observation_message(pending["command"], "en"), request_id=pending["record_id"])
                    del self._pending_commands[key]
                elif status in {"timeout", "write_error", "reset_error", "disconnected", "endpoint_changed", "feedback_lost", "stale_or_endpoint_changed", "superseded", "superseded_by_stop", "no_fresh_transition"}:
                    detail = ("Não foi possível confirmar o pedido pelo estado do PLC."
                              if self._ui_lang == "pt" else "The request could not be confirmed by the PLC state.")
                    self._add_event(pending["command"], "opcua", False, detail, reason=status,
                                    detail_pt="Não foi possível confirmar o pedido pelo estado do PLC.",
                                    detail_en="The request could not be confirmed by the PLC state.", request_id=pending["record_id"])
                    del self._pending_commands[key]

    def pending_snapshot(self) -> dict[str, dict]:
        self._synchronize_plc()
        with self._lock:
            return {key: dict(value) for key, value in self._pending_commands.items()}

    @property
    def control_mode(self) -> str:
        return self._control_mode

    def _publish_control_mode(self):
        self._publish("monitor/control_mode", self._control_mode)
        self._publish("monitor/pt/control_mode", "Teste local; sem confirmação do PLC" if self._control_mode == "test"
                      else "Sincronizado com o PLC")
        self._publish("monitor/en/control_mode", "Local test; not confirmed by PLC" if self._control_mode == "test"
                      else "Synchronized with PLC")

    def set_control_mode(self, mode: str) -> bool:
        if mode not in {"plc", "test"}:
            return False
        self._synchronize_plc()
        health = self._opcua.health() if hasattr(self._opcua, "health") else {}
        available = bool(health.get("connected") and health.get("feedback_active"))
        projected, quality = project_plc_state(dict(health.get("received") or {}), available)
        with self._lock:
            if mode == self._control_mode:
                return True
            # Do not change semantics while a physical write may still be pending.
            if self._pending_commands:
                return False
            self._cancel_test_pulses()
            self._control_mode = mode
            self._plc_available = available
            self._plc_epoch = health.get("feedback_epoch")
            self._plc_received = dict(health.get("received") or {}) if available else {}
            if projected["system_error"] is not None:
                self._plc_error_latched = bool(self._plc_received.get("system_error"))
            self._last_known = {key: value for key, value in projected.items() if value is not None}
            new_state = {key: 0 for key in STATE_KEYS} if mode == "test" else projected
            new_quality = {key: "local" for key in STATE_KEYS} if mode == "test" else quality
            self._publish_control_mode()
            for key in STATE_KEYS:
                self.state[key] = new_state[key]
                self.state_quality[key] = new_quality[key]
                self._publish(f"state/{key}", new_state[key] if new_state[key] is not None else "unknown", retain=True)
                self._publish(f"state_quality/{key}", new_quality[key], retain=True)
            pt = ("Modo de teste ativo. Os comandos continuam a ser enviados ao PLC quando ligado; os estados apresentados são locais, sem confirmação."
                  if mode == "test" else "Modo sincronizado ativo. Os estados voltam a depender do retorno do PLC.")
            en = ("Test mode active. Commands are still sent to the PLC when connected; displayed states are local and unconfirmed."
                  if mode == "test" else "Synchronized mode active. States now depend on PLC feedback again.")
            self._add_event("CONTROL_MODE", "button", True, pt if self._ui_lang == "pt" else en,
                            reason="control_mode", detail_pt=pt, detail_en=en)
        return True

    def _apply_local_command(self, command: str, key: str, value: int):
        changes = {}
        if command == "STOP":
            self._cancel_test_pulses()
            changes = {item: 0 for item in STATE_KEYS}
        elif command in {"MODE_FAST", "MODE_IDEAL", "MODE_MANUAL", "MODE_UNSPEC"}:
            self._cancel_test_pulses()
            changes = {item: 0 for item in ("mode_fast", "mode_ideal", "mode_manual", "mode_change")}
            changes[key] = value
            if command == "MODE_UNSPEC":
                changes.update({item: 0 for item in STATE_KEYS if item.startswith(("motor_", "cyl_", "light_", "robot_"))})
        else:
            changes[key] = value
            if command in {"ROBOT_TO_METAL", "ROBOT_TO_NONMETAL"}:
                other_key = "robot_nonmetal" if key == "robot_metal" else "robot_metal"
                self._cancel_test_pulses({other_key})
                changes[other_key] = 0
        for item, new_value in changes.items():
            if self.state[item] != new_value:
                self.state[item] = new_value
                self._publish(f"state/{item}", new_value, retain=True)

    def _cancel_test_pulses(self, keys: set[str] | None = None):
        for key in tuple(self._test_pulses):
            if keys is not None and key not in keys:
                continue
            timer, topic = self._test_pulses.pop(key)
            timer.cancel()
            self._publish(topic, "0", retain=False, suppress_echo=True)

    def _schedule_test_pulse(self, key: str, command: str):
        outbound = command_outbound_payload(command)
        if not outbound:
            return
        topic = outbound[0]

        def release():
            with self._lock:
                if self._test_pulses.get(key, (None,))[0] is not timer:
                    return
                del self._test_pulses[key]
                self._publish(topic, "0", retain=False, suppress_echo=True)
                if self._control_mode == "test" and self.state[key] == 1:
                    self.state[key] = 0
                    self._publish(f"state/{key}", 0, retain=True)

        timer = threading.Timer(_TEST_PULSE_SECONDS, release)
        timer.daemon = True
        self._test_pulses[key] = (timer, topic)
        timer.start()

    def process_command(
        self,
        command: str,
        lang: str,
        source: str = "voice",
        emit_pulse: Optional[bool] = None,
        bypass_workflow: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        self._synchronize_plc()
        with self._lock:
            self._publish(
                "events/last_command",
                json.dumps({"command": command, "source": source}, ensure_ascii=True),
                retain=True,
            )
            reason = ""
            target = command_target(command)
            if command in {"UNKNOWN", "NO_AUDIO"}:
                reason = "no_audio" if command == "NO_AUDIO" else "unknown"
            elif command in {"CYL_C_RETRACT", "CYL_D_RETRACT"}:
                reason = "cylinder_retract_unavailable"
            elif target is None or command not in COMMAND_TO_NODE:
                reason = "unknown"
            elif (self.state.get("system_error") == 1 or self._plc_error_latched) and command != "STOP":
                reason = "system_error"
            else:
                reason = self._workflow_rejection_reason(command) or ""
            if not reason and target is not None:
                key, value = target
                same_group_pending = (key in self._pending_commands
                                      or key.startswith("mode_") and any(item.startswith("mode_") for item in self._pending_commands))
                if command != "STOP" and (same_group_pending or command == "MODE_UNSPEC" and self._pending_commands):
                    reason = "command_pending"
                elif self.state.get(key) == value and not (command == "STOP" and "start" in self._pending_commands):
                    reason = "no_change"
            if reason:
                msg = rejection_message(reason, lang, command)
                self._publish_rejected(command, reason)
                self._add_event(command=command, source=source, accepted=False, detail=msg, reason=reason)
                return False, msg

            record_id = self._opcua.enqueue_command(command, source=source)
            if record_id is False and self._control_mode == "plc":
                reason = "opcua_unavailable"
                msg = rejection_message(reason, lang, command)
                self._publish_rejected(command, reason)
                self._add_event(command=command, source=source, accepted=False, detail=msg, reason=reason)
                return False, msg
            key, value = target
            if self._control_mode == "test":
                self._apply_local_command(command, key, value)
                if command in _TEST_PULSE_COMMANDS:
                    self._emit_command_level(command)
                    self._schedule_test_pulse(key, command)
                else:
                    self._emit_for_command(command, emit_pulse)
                pt = self._response_for_command(command, "pt")
                en = self._response_for_command(command, "en")
                if record_id is False:
                    pt += " Envio OPC UA não realizado; comando não chegou à maquete por esta via."
                    en += " OPC UA send failed; the command did not reach the machine by this route."
                self._add_event(command, source, True, pt if lang == "pt" else en,
                                reason="local_sent" if record_id is not False else "local_only",
                                detail_pt=pt, detail_en=en)
                return True, pt if lang == "pt" else en
            if command == "STOP" and "start" in self._pending_commands:
                self._add_event(self._pending_commands["start"]["command"], "opcua", False,
                                "Pedido anterior substituído por paragem." if lang == "pt" else "Previous request superseded by stop.",
                                reason="superseded_by_stop", request_id=self._pending_commands["start"]["record_id"])
            self._pending_commands[key] = {
                "command": command, "target": value, "record_id": record_id or 0,
                "source": source, "stage": "queued", "created_at": time.monotonic(),
            }
            self._emit_for_command(command, emit_pulse)
            self._add_event(
                command=command, source=source, accepted=True,
                detail=self._response_for_command(command, lang), reason="queued", request_id=record_id,
            )
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

    def _is_component_command(self, command: str) -> bool:
        return (
            bool(re.match(r"^MOTOR_([123])_(ON|OFF)$", command))
            or bool(re.match(r"^CYL_([ABCD])_(EXTEND|RETRACT)$", command))
            or command in {"GREEN_ON", "GREEN_OFF", "RED_ON", "RED_OFF", "ROBOT_TO_METAL", "ROBOT_TO_NONMETAL"}
        )

    def _workflow_state(self) -> dict:
        # Pending intent guides command order, but never changes the displayed PLC state.
        keys = ("start", "mode_fast", "mode_ideal", "mode_manual", "mode_change")
        state = {key: self.state[key] for key in keys}
        if self._control_mode == "plc":
            for key in keys:
                pending = self._pending_commands.get(key)
                if pending is None:
                    continue
                if key.startswith("mode_"):
                    for mode_key in keys[1:]:
                        state[mode_key] = 0
                state[key] = pending["target"]
        return state

    def _workflow_rejection_reason(self, command: str) -> Optional[str]:
        if command in {"UNKNOWN", "NO_AUDIO", "START", "STOP"}:
            return None
        state = self._workflow_state()
        if state["start"] != 1:
            return "before_start"

        mode = next((key[5:] for key in ("mode_fast", "mode_ideal", "mode_manual", "mode_change")
                     if state[key] == 1), "none")

        if mode == "none":
            if command in {"MODE_FAST", "MODE_IDEAL", "MODE_MANUAL"}:
                return None
            return "choose_mode"

        if mode == "change":
            if command in {"MODE_FAST", "MODE_IDEAL", "MODE_MANUAL"}:
                return None
            return "choose_new_mode"

        if mode in {"fast", "ideal"}:
            if command == "MODE_UNSPEC":
                return None
            if command in {"MODE_FAST", "MODE_IDEAL", "MODE_MANUAL"}:
                if (mode == "fast" and command == "MODE_FAST") or (mode == "ideal" and command == "MODE_IDEAL"):
                    return None
                return "change_mode_first"
            if self._is_component_command(command):
                return "manual_only"
            return None

        if mode == "manual":
            if command == "MODE_UNSPEC":
                return None
            if command in {"MODE_FAST", "MODE_IDEAL"}:
                return "change_mode_first"
            return None

        return None

    def _workflow_message_invalid(self, command: str, lang: str) -> Optional[str]:
        reason = self._workflow_rejection_reason(command)
        return rejection_message(reason, lang) if reason else None

    def _no_change_message(self, command: str, lang: str) -> str:
        return no_change_message(command, lang)

    def _response_for_command(self, command: str, lang: str) -> str:
        label = command_label(command, lang)
        if self._control_mode == "test":
            return (f"Pedido para {label} aceite. Estado local, não confirmado pelo PLC."
                    if lang == "pt" else f"Request to {label} accepted. Local state, not confirmed by the PLC.")
        return (f"Pedido para {label} colocado na fila. Aguarda confirmação do PLC."
                if lang == "pt" else f"Request to {label} queued. Awaiting the PLC state.")

    def _add_event(self, command: str, source: str, accepted: bool, detail: Optional[str], reason: str = "",
                   detail_pt: str = "", detail_en: str = "", plc_key: str = "", plc_value: int | None = None,
                   request_pending: bool = False, request_id: int | None = None):
        event = {
            "id": self._next_event_id,
            "time": datetime.now().strftime("%H:%M:%S"),
            "source": source,
            "command": command,
            "accepted": accepted,
            "detail": detail or "",
            "detail_pt": detail_pt,
            "detail_en": detail_en,
            "plc_key": plc_key,
            "plc_value": plc_value,
            "request_pending": request_pending,
            "request_id": request_id,
            "reason": reason,
            "generation": self._event_generation,
        }
        self._next_event_id += 1
        self._events.append(event)
        self._publish_monitor_event(event)

    def _publish_monitor_event(self, event: dict):
        for lang in ("pt", "en"):
            message = self._event_monitor_message(event, lang)
            self._publish(f"monitor/{lang}/last_message", message)
            if event["source"] == "mqtt_text":
                self._publish(f"monitor/{lang}/phone_textbot_response", message)
        self._publish("monitor/last_event_status", "ok" if event["accepted"] else "rejected")
        self._publish("monitor/last_event_stage", event.get("reason") or ("accepted" if event["accepted"] else "rejected"))

    def _publish_phone_event(self, event: dict):
        for lang in ("pt", "en"):
            self._publish(f"monitor/{lang}/phone_textbot_response", self._event_monitor_message(event, lang))

    def _event_monitor_message(self, event: dict, lang: str) -> str:
        if event.get("kind") in {"query", "setting"}:
            return str(event.get(f"detail_{lang}") or event.get("detail") or "")
        if event.get("source") in {"plc", "opcua"}:
            return str(event.get(f"detail_{lang}") or event.get("detail") or "")
        if not event["accepted"]:
            return rejection_for_event(event, lang)
        if event.get(f"detail_{lang}"):
            return str(event[f"detail_{lang}"])
        if event["command"] == "SYSTEM_RESET":
            return "Sessão reiniciada; o PLC não foi alterado." if lang == "pt" else "Session restarted; PLC state unchanged."
        if event["command"] == "SYSTEM_SHUTDOWN":
            return "Sistema a desligar." if lang == "pt" else "System shutting down."
        message = self._response_for_command(event["command"], lang)
        if message == event["command"]:
            return "Pedido executado." if lang == "pt" else "Request completed."
        return message

    def last_event_message(self, lang: str) -> str:
        with self._lock:
            return self._event_monitor_message(self._events[-1], lang) if self._events else ""

    def remember_interaction_response(self, response: str, lang: str, speech: str = ""):
        if response:
            with self._lock:
                self._last_interaction_response[lang] = response
                if speech:
                    if not hasattr(self, "_last_speech_response"):
                        self._last_speech_response = {"pt": "", "en": ""}
                    self._last_speech_response[lang] = speech

    def answer_status_query(self, name: str, component: str, lang: str, source: str, value: str = "") -> str:
        return self.answer_status_query_parts(name, component, lang, source, value)["detail"]

    def answer_status_query_parts(self, name: str, component: str, lang: str, source: str,
                                  value: str = "") -> dict[str, str]:
        if (name not in VALID_QUERIES or
                (name == "QUERY_COMPONENT" and component not in VALID_COMPONENTS) or
                (name == "QUERY_COMPONENT_GROUP" and component not in VALID_GROUPS) or
                name == "QUERY_SETTING"):
            message = rejection_message("unknown", lang)
            return {"speech": message, "detail": message, "localized_speech": {
                language: rejection_message("unknown", language) for language in ("pt", "en")
            }}
        health = self.health()
        try:
            from blanky.speech_service import is_openai_configured
            health["openai_configured"] = is_openai_configured()
        except ImportError:
            health["openai_configured"] = bool(os.environ.get("OPENAI_API_KEY"))
        health["openai_activity"] = activity_snapshot()
        with self._lock:
            state = dict(self.state)
            events = list(self._events)
            if events:
                events[-1] = {**events[-1], **{
                    f"detail_{language}": self._event_monitor_message(events[-1], language)
                    for language in ("pt", "en")
                }}
            allowed = {command for command in VALID_COMMANDS
                       if command in COMMAND_TO_NODE and (health.get("opcua_connected") or self._control_mode == "test")
                       and (not self._plc_error_latched or command == "STOP")
                       and self._workflow_rejection_reason(command) is None}
            if name == "QUERY_OPTIONS":
                state.update(self._workflow_state())
            previous = dict(self._last_interaction_response)
            answers = {
                language: answer_query_parts(name, component, value, language, state, health, events, allowed,
                                             previous[language])
                for language in ("pt", "en")
            }
            if name == "REPEAT":
                previous_speech = getattr(self, "_last_speech_response", {})
                for language in ("pt", "en"):
                    if previous_speech.get(language):
                        answers[language]["speech"] = previous_speech[language]
            event = {
                "id": self._next_event_id, "time": datetime.now().strftime("%H:%M:%S"),
                "source": source, "command": name, "kind": "query", "accepted": True,
                "detail": answers[lang]["detail"], "detail_pt": answers["pt"]["detail"],
                "detail_en": answers["en"]["detail"],
                "speech_pt": answers["pt"]["speech"], "speech_en": answers["en"]["speech"],
                "reason": "", "generation": self._event_generation,
            }
            self._next_event_id += 1
            self._events.append(event)
            self._publish_monitor_event(event)
        return {**answers[lang], "localized_speech": {
            language: answers[language]["speech"] for language in ("pt", "en")
        }}

    def record_preference_event(self, source: str, answers: dict[str, dict[str, str]],
                                accepted: bool = True, kind: str = "setting"):
        """Log a UI preference without entering the command/OPC UA path."""
        with self._lock:
            event = {
                "id": self._next_event_id, "time": datetime.now().strftime("%H:%M:%S"),
                "source": source, "command": "SET_SETTING" if kind == "setting" else "QUERY_SETTING",
                "kind": kind,
                "accepted": accepted, "detail": answers["pt"]["detail"],
                "detail_pt": answers["pt"]["detail"], "detail_en": answers["en"]["detail"],
                "speech_pt": answers["pt"]["speech"], "speech_en": answers["en"]["speech"],
                "reason": "", "generation": self._event_generation,
            }
            self._next_event_id += 1
            self._events.append(event)
            self._publish_monitor_event(event)

    def reset_system(self, lang: str, source: str = "button") -> Tuple[bool, str]:
        with self._lock:
            # Preserve all existing events, but make subsequent events part of a new session.
            self._event_generation += 1
            msg = (
                "Sessão do Blanky reiniciada. O estado do PLC não foi alterado."
                if lang == "pt"
                else "Blanky session restarted. The PLC state was not changed."
            )
            self._add_event(command="SYSTEM_RESET", source=source, accepted=True, detail=msg)
            return True, msg

    def shutdown_system(self, lang: str, source: str = "button") -> Tuple[bool, str]:
        with self._lock:
            msg = "Sistema a desligar." if lang == "pt" else "System shutting down."
            self._add_event(command="SYSTEM_SHUTDOWN", source=source, accepted=True, detail=msg)
            return True, msg

    def response_for_command(self, command: str, lang: str) -> str:
        return self._response_for_command(command, lang)

    def get_snapshot(self) -> dict[str, Any]:
        self._synchronize_plc()
        with self._lock:
            return {
                "state": dict(self.state),
                "workflow": self._workflow_state(),
                "state_quality": dict(self.state_quality),
                "control_mode": self._control_mode,
                "pending": {key: dict(value) for key, value in self._pending_commands.items()},
                "plc_received": dict(self._plc_received),
                "plc_available": self._plc_available,
                "last_valid_read": self._last_valid_read,
                "events": list(self._events),
                "event_generation": self._event_generation,
            }

    def health(self) -> dict[str, Any]:
        self._synchronize_plc()
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
            "control_mode": self._control_mode,
            "opcua_last_error": str(opcua_health.get("last_error") or ""),
            "opcua_last_write": str(opcua_health.get("last_write") or ""),
            "opcua_feedback_active": bool(opcua_health.get("feedback_active")),
            "opcua_feedback_count": opcua_health.get("feedback_count", 0),
            "opcua_feedback_null_count": opcua_health.get("feedback_null_count", 0),
            "opcua_feedback_total": opcua_health.get("feedback_total", 0),
            "opcua_initial_complete": bool(opcua_health.get("initial_complete")),
            "opcua_last_valid_read": str(opcua_health.get("last_valid_read") or ""),
            "opcua_plc_path_verified": False,
            "opcua_feedback_error": str(opcua_health.get("feedback_error") or ""),
            "opcua_last_feedback": str(opcua_health.get("last_feedback") or ""),
            "opcua_last_write_ms": opcua_health.get("last_write_ms"),
            "opcua_last_ack_ms": opcua_health.get("last_ack_ms"),
            "opcua_received": opcua_health.get("received", {}),
            "opcua_url": str(opcua_health.get("url") or ""),
            "mqtt_host": self._broker_host,
            "mqtt_port": self._broker_port,
            "mqtt_topic_prefix": self._topic_prefix,
            "mqtt_client_id": self._client_id,
        }

    def opcua_timing_records(self) -> list[dict]:
        return self._opcua.timing_records()

    def set_ui_lang(self, lang: str):
        with self._lock:
            self._ui_lang = "pt" if lang not in {"pt", "en"} else lang


_BRIDGE: Optional[MQTTBridge] = None


def get_mqtt_bridge() -> MQTTBridge:
    global _BRIDGE
    if _BRIDGE is None:
        _BRIDGE = MQTTBridge()
    return _BRIDGE
