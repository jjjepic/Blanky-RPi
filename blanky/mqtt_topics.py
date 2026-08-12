from __future__ import annotations

from typing import Dict, Optional, Tuple


COMMAND_TO_TOPIC: Dict[str, str] = {
    "START": "mqtt_start",
    "STOP": "mqtt_stop",
    "MODE_FAST": "mqtt_mode_fast",
    "MODE_IDEAL": "mqtt_mode_ideal",
    "MODE_MANUAL": "mqtt_mode_manual",
    "MODE_UNSPEC": "mqtt_mode_change",
    "MOTOR_1_ON": "mqtt_motor_1",
    "MOTOR_1_OFF": "mqtt_motor_1",
    "MOTOR_2_ON": "mqtt_motor_2",
    "MOTOR_2_OFF": "mqtt_motor_2",
    "MOTOR_3_ON": "mqtt_motor_3",
    "MOTOR_3_OFF": "mqtt_motor_3",
    "CYL_A_EXTEND": "mqtt_cyl_a",
    "CYL_A_RETRACT": "mqtt_cyl_a",
    "CYL_B_EXTEND": "mqtt_cyl_b",
    "CYL_B_RETRACT": "mqtt_cyl_b",
    "CYL_C_EXTEND": "mqtt_cyl_c",
    "CYL_C_RETRACT": "mqtt_cyl_c",
    "CYL_D_EXTEND": "mqtt_cyl_d",
    "CYL_D_RETRACT": "mqtt_cyl_d",
    "GREEN_ON": "mqtt_green",
    "GREEN_OFF": "mqtt_green",
    "RED_ON": "mqtt_red",
    "RED_OFF": "mqtt_red",
    "ROBOT_TO_METAL": "mqtt_robot_to_metal",
    "ROBOT_TO_NONMETAL": "mqtt_robot_to_nonmetal",
}

TOPIC_TRUE_TO_COMMAND: Dict[str, str] = {
    "mqtt_start": "START",
    "mqtt_stop": "STOP",
    "mqtt_mode_fast": "MODE_FAST",
    "mqtt_mode_ideal": "MODE_IDEAL",
    "mqtt_mode_manual": "MODE_MANUAL",
    "mqtt_mode_change": "MODE_UNSPEC",
    "mqtt_motor_1": "MOTOR_1_ON",
    "mqtt_motor_2": "MOTOR_2_ON",
    "mqtt_motor_3": "MOTOR_3_ON",
    "mqtt_cyl_a": "CYL_A_EXTEND",
    "mqtt_cyl_b": "CYL_B_EXTEND",
    "mqtt_cyl_c": "CYL_C_EXTEND",
    "mqtt_cyl_d": "CYL_D_EXTEND",
    "mqtt_green": "GREEN_ON",
    "mqtt_red": "RED_ON",
    "mqtt_robot_to_metal": "ROBOT_TO_METAL",
    "mqtt_robot_to_nonmetal": "ROBOT_TO_NONMETAL",
}

TOPIC_FALSE_TO_COMMAND: Dict[str, str] = {
    "mqtt_motor_1": "MOTOR_1_OFF",
    "mqtt_motor_2": "MOTOR_2_OFF",
    "mqtt_motor_3": "MOTOR_3_OFF",
    "mqtt_cyl_a": "CYL_A_RETRACT",
    "mqtt_cyl_b": "CYL_B_RETRACT",
    "mqtt_cyl_c": "CYL_C_RETRACT",
    "mqtt_cyl_d": "CYL_D_RETRACT",
    "mqtt_green": "GREEN_OFF",
    "mqtt_red": "RED_OFF",
}


def topic_for_command(command: str) -> Optional[str]:
    return COMMAND_TO_TOPIC.get(command)


def payload_to_bool(payload: str) -> Optional[bool]:
    value = (payload or "").strip().lower()
    if value in {"1", "on", "true", "high", "pulse"}:
        return True
    if value in {"0", "off", "false", "low"}:
        return False
    return None


def command_for_topic_payload(topic_suffix: str, payload: str) -> Optional[str]:
    value = payload_to_bool(payload)
    if value is True:
        return TOPIC_TRUE_TO_COMMAND.get(topic_suffix)
    if value is False:
        return TOPIC_FALSE_TO_COMMAND.get(topic_suffix)
    return None


def command_outbound_payload(command: str) -> Optional[Tuple[str, str]]:
    topic = topic_for_command(command)
    if not topic:
        return None

    if command.endswith("_ON") or command.endswith("_EXTEND"):
        return topic, "1"
    if command.endswith("_OFF") or command.endswith("_RETRACT"):
        return topic, "0"
    return topic, "1"


def should_use_pulse(command: str) -> bool:
    no_pulse_prefixes = ("MOTOR_", "CYL_", "GREEN_", "RED_")
    return not command.startswith(no_pulse_prefixes)
