"""Interpret PLC return bits without confusing requests with observations."""

from __future__ import annotations

STATE_KEYS = (
    "start", "mode_fast", "mode_ideal", "mode_manual", "mode_change",
    "motor_1", "motor_2", "motor_3", "cyl_a", "cyl_b", "cyl_c", "cyl_d",
    "light_green", "light_red", "robot_metal", "robot_nonmetal", "system_error",
)


def command_target(command: str) -> tuple[str, int] | None:
    fixed = {
        "START": ("start", 1), "STOP": ("start", 0),
        "MODE_FAST": ("mode_fast", 1), "MODE_IDEAL": ("mode_ideal", 1),
        "MODE_MANUAL": ("mode_manual", 1), "MODE_UNSPEC": ("mode_change", 1),
        "GREEN_ON": ("light_green", 1), "GREEN_OFF": ("light_green", 0),
        "RED_ON": ("light_red", 1), "RED_OFF": ("light_red", 0),
        "ROBOT_TO_METAL": ("robot_metal", 1),
        "ROBOT_TO_NONMETAL": ("robot_nonmetal", 1),
    }
    if command in fixed:
        return fixed[command]
    parts = command.split("_")
    if len(parts) == 3 and parts[0] == "MOTOR" and parts[1] in {"1", "2", "3"} and parts[2] in {"ON", "OFF"}:
        return f"motor_{parts[1]}", int(parts[2] == "ON")
    if len(parts) == 3 and parts[0] == "CYL" and parts[1] in {"A", "B", "C", "D"} and parts[2] in {"EXTEND", "RETRACT"}:
        return f"cyl_{parts[1].lower()}", int(parts[2] == "EXTEND")
    return None


def _pair(values: dict[str, bool], positive: str, negative: str) -> int | None:
    on, off = values.get(positive), values.get(negative)
    if on is True and off is False:
        return 1
    if on is False and off is True:
        return 0
    return None


def project_plc_state(received: dict[str, bool], available: bool) -> tuple[dict[str, int | None], dict[str, str]]:
    """Return confirmed values and quality; None never means a confirmed OFF."""
    state = {key: None for key in STATE_KEYS}
    quality = {key: "unavailable" for key in STATE_KEYS}
    if not available:
        return state, quality

    pairs = {
        "start": ("system_on", "system_stopped"),
        "motor_1": ("motor_1_on", "motor_1_off"),
        "motor_2": ("motor_2_on", "motor_2_off"),
        "motor_3": ("motor_3_on", "motor_3_off"),
        "cyl_a": ("cyl_a_advanced", "cyl_a_retracted"),
        "cyl_b": ("cyl_b_advanced", "cyl_b_retracted"),
        "light_green": ("green_on", "green_off"),
        "light_red": ("red_on", "red_off"),
    }
    for key, (positive, negative) in pairs.items():
        if positive not in received or negative not in received:
            continue
        state[key] = _pair(received, positive, negative)
        quality[key] = "confirmed" if state[key] is not None else "inconsistent"

    modes = ("mode_fast", "mode_ideal", "mode_manual", "mode_change")
    if all(key in received for key in modes):
        if sum(received[key] for key in modes) <= 1:
            for key in modes:
                state[key] = int(received[key])
                quality[key] = "confirmed"
        else:
            for key in modes:
                quality[key] = "inconsistent"

    for key, signal in (("cyl_c", "cyl_c_advance_signal"), ("cyl_d", "cyl_d_advance_signal")):
        if signal not in received:
            continue
        if received[signal]:
            state[key], quality[key] = 1, "confirmed"
        else:
            quality[key] = "position_unknown"

    for key in ("robot_metal", "robot_nonmetal", "system_error"):
        if key in received:
            state[key] = int(received[key])
            quality[key] = "confirmed"
    return state, quality
