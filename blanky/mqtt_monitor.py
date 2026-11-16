"""Read-only MQTT presentation topics; command and legacy state topics stay unchanged."""


def _mode(state: dict) -> str:
    if state["start"] is None or any(state[key] is None for key in ("mode_fast", "mode_ideal", "mode_manual", "mode_change")):
        return "unknown"
    if state["start"] == 0:
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
        "unknown": "Estado não confirmado",
        "stopped": "Sistema parado",
        "choose_mode": "Escolhe um modo",
        "fast": "Modo rápido",
        "ideal": "Modo ideal",
        "manual": "Modo manual",
        "changing": "Escolhe o novo modo",
    },
    "en": {
        "unknown": "State unconfirmed",
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
        updates["monitor/pt/system"] = "Não confirmado" if state[key] is None else "Iniciado" if state[key] else "Parado"
        updates["monitor/en/system"] = "Unconfirmed" if state[key] is None else "Started" if state[key] else "Stopped"

    if key == "start" or key.startswith("mode_"):
        mode = _mode(state)
        updates["monitor/mode"] = mode
        for lang in ("pt", "en"):
            updates[f"monitor/{lang}/mode"] = _MODE_TEXT[lang][mode]

    if key.startswith("motor_"):
        updates[f"monitor/pt/{key}"] = "Não confirmado" if state[key] is None else "Ligado" if state[key] else "Desligado"
        updates[f"monitor/en/{key}"] = "Unconfirmed" if state[key] is None else "On" if state[key] else "Off"
    elif key.startswith("cyl_"):
        updates[f"monitor/pt/{key}"] = "Posição não confirmada" if state[key] is None else "Avançado" if state[key] else "Recolhido"
        updates[f"monitor/en/{key}"] = "Position unconfirmed" if state[key] is None else "Extended" if state[key] else "Retracted"
    elif key.startswith("light_"):
        updates[f"monitor/pt/{key}"] = "Não confirmado" if state[key] is None else "Acesa" if state[key] else "Apagada"
        updates[f"monitor/en/{key}"] = "Unconfirmed" if state[key] is None else "On" if state[key] else "Off"
    elif key.startswith("robot_"):
        if state["robot_metal"] is None or state["robot_nonmetal"] is None:
            updates["monitor/pt/robot"] = "Pedido não confirmado"
            updates["monitor/en/robot"] = "Request unconfirmed"
        elif state["robot_metal"] and state["robot_nonmetal"]:
            updates["monitor/pt/robot"] = "Pedidos de recolha nos Tapetes 2 e 3"
            updates["monitor/en/robot"] = "Pickup requests on Conveyors 2 and 3"
        elif state["robot_metal"]:
            updates["monitor/pt/robot"] = "Pedido de recolha no Tapete 2"
            updates["monitor/en/robot"] = "Pickup request on Conveyor 2"
        elif state["robot_nonmetal"]:
            updates["monitor/pt/robot"] = "Pedido de recolha no Tapete 3"
            updates["monitor/en/robot"] = "Pickup request on Conveyor 3"
        else:
            updates["monitor/pt/robot"] = "Sem pedido de recolha"
            updates["monitor/en/robot"] = "No pickup request"
    elif key == "system_error":
        updates["monitor/pt/system_error"] = "Não confirmado" if state[key] is None else "Erro ativo" if state[key] else "Sem erro ativo"
        updates["monitor/en/system_error"] = "Unconfirmed" if state[key] is None else "Error active" if state[key] else "No active error"

    return updates


def health_monitor_updates(health: dict) -> dict[str, str]:
    """OPC UA connection is distinct from PLC feedback and command receipt."""
    feedback_active = bool(health.get("opcua_feedback_active"))
    write_ms = health.get("opcua_last_write_ms")
    ack_ms = health.get("opcua_last_ack_ms") if feedback_active else None
    return {
        "monitor/opcua": "connected" if health.get("opcua_connected") else "disconnected",
        "monitor/opcua_feedback": "active" if feedback_active else "unavailable",
        "monitor/plc_path": "unverified",
        "monitor/pt/opcua": "Ligado" if health.get("opcua_connected") else "Desligado",
        "monitor/en/opcua": "Connected" if health.get("opcua_connected") else "Disconnected",
        "monitor/pt/opcua_feedback": "Ativo" if feedback_active else "Indisponível",
        "monitor/en/opcua_feedback": "Active" if feedback_active else "Unavailable",
        "monitor/pt/plc_path": "Percurso entre PLCs não verificável sem heartbeat",
        "monitor/en/plc_path": "Inter-PLC path cannot be verified without a heartbeat",
        "monitor/pt/opcua_write_time": f"{write_ms:.2f} ms" if write_ms is not None else "Sem medição",
        "monitor/en/opcua_write_time": f"{write_ms:.2f} ms" if write_ms is not None else "No measurement",
        "monitor/pt/opcua_ack_time": f"{ack_ms:.2f} ms" if ack_ms is not None else "Sem confirmação",
        "monitor/en/opcua_ack_time": f"{ack_ms:.2f} ms" if ack_ms is not None else "No confirmation",
    }
