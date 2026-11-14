"""Read-only MQTT presentation topics; command and legacy state topics stay unchanged."""


def _mode(state: dict) -> str:
    if not state["start"]:
        return "stopped"
    for key, value in (
        ("mode_fast", "fast"),
        ("mode_ideal", "ideal"),
        ("mode_manual", "manual"),
        ("mode_change", "changing"),
    ):
        if state[key]:
            return value
    return "choose_mode"


_MODE_TEXT = {
    "pt": {
        "stopped": "Sistema parado",
        "choose_mode": "Escolhe um modo",
        "fast": "Modo rápido",
        "ideal": "Modo ideal",
        "manual": "Modo manual",
        "changing": "Escolhe o novo modo",
    },
    "en": {
        "stopped": "System stopped",
        "choose_mode": "Choose a mode",
        "fast": "Fast mode",
        "ideal": "Ideal mode",
        "manual": "Manual mode",
        "changing": "Choose the new mode",
    },
}


def state_monitor_updates(state: dict, key: str) -> dict[str, str]:
    """Return only the presentation topics affected by one legacy state update."""
    updates = {}
    if key == "start":
        updates["monitor/pt/system"] = "Iniciado" if state[key] else "Parado"
        updates["monitor/en/system"] = "Started" if state[key] else "Stopped"

    if key == "start" or key.startswith("mode_"):
        mode = _mode(state)
        updates["monitor/mode"] = mode
        for lang in ("pt", "en"):
            updates[f"monitor/{lang}/mode"] = _MODE_TEXT[lang][mode]

    if key.startswith("motor_"):
        updates[f"monitor/pt/{key}"] = "Ligado" if state[key] else "Desligado"
        updates[f"monitor/en/{key}"] = "On" if state[key] else "Off"
    elif key.startswith("cyl_"):
        updates[f"monitor/pt/{key}"] = "Avanço solicitado" if state[key] else "Recuo solicitado"
        updates[f"monitor/en/{key}"] = "Extend requested" if state[key] else "Retract requested"
    elif key.startswith("light_"):
        updates[f"monitor/pt/{key}"] = "Acesa" if state[key] else "Apagada"
        updates[f"monitor/en/{key}"] = "On" if state[key] else "Off"
    elif key.startswith("robot_"):
        if state["robot_metal"]:
            updates["monitor/pt/robot"] = "Destino: peças metálicas"
            updates["monitor/en/robot"] = "Target: metal pieces"
        elif state["robot_nonmetal"]:
            updates["monitor/pt/robot"] = "Destino: peças não metálicas"
            updates["monitor/en/robot"] = "Target: non-metal pieces"
        else:
            updates["monitor/pt/robot"] = "Sem destino ativo"
            updates["monitor/en/robot"] = "No active target"

    return updates


def health_monitor_updates(health: dict) -> dict[str, str]:
    """OPC UA connection is distinct from PLC feedback and command receipt."""
    feedback_active = bool(health.get("opcua_feedback_active"))
    write_ms = health.get("opcua_last_write_ms")
    ack_ms = health.get("opcua_last_ack_ms") if feedback_active else None
    return {
        "monitor/opcua": "connected" if health.get("opcua_connected") else "disconnected",
        "monitor/opcua_feedback": "active" if feedback_active else "unavailable",
        "monitor/pt/opcua": "Ligado" if health.get("opcua_connected") else "Desligado",
        "monitor/en/opcua": "Connected" if health.get("opcua_connected") else "Disconnected",
        "monitor/pt/opcua_feedback": "Ativo" if feedback_active else "Indisponível",
        "monitor/en/opcua_feedback": "Active" if feedback_active else "Unavailable",
        "monitor/pt/opcua_write_time": f"{write_ms:.2f} ms" if write_ms is not None else "Sem medição",
        "monitor/en/opcua_write_time": f"{write_ms:.2f} ms" if write_ms is not None else "No measurement",
        "monitor/pt/opcua_ack_time": f"{ack_ms:.2f} ms" if ack_ms is not None else "Sem confirmação",
        "monitor/en/opcua_ack_time": f"{ack_ms:.2f} ms" if ack_ms is not None else "No confirmation",
    }
