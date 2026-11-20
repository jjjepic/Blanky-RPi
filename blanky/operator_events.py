"""Operator-facing summaries without changing the technical event history."""

from blanky.command_messages import command_label
from blanky.plc_state import command_target


def pending_message(command: str, lang: str) -> str:
    action = command_label(command, lang)
    action = action[:1].upper() + action[1:]
    return f"{action} · {'A confirmar' if lang == 'pt' else 'Awaiting confirmation'}"


def _state_message(key: str, value: int, lang: str) -> str:
    pt = lang == "pt"
    if key == "start":
        return ("Sistema ligado." if value else "Sistema parado.") if pt else ("System on." if value else "System stopped.")
    if key == "system_error":
        return ("Erro no sistema." if value else "Erro do sistema limpo.") if pt else ("System error." if value else "System error cleared.")
    modes = {"mode_fast": ("rápido", "Fast"), "mode_ideal": ("ideal", "Ideal"),
             "mode_manual": ("manual", "Manual"), "mode_change": ("de mudança", "Change")}
    if key in modes:
        return (f"Modo {modes[key][0]} {'ativo' if value else 'inativo'}." if pt else
                f"{modes[key][1]} mode {'active' if value else 'inactive'}.")
    if key.startswith("motor_"):
        return (f"Saída do motor {key[-1]} {'ligada' if value else 'desligada'}." if pt else
                f"Motor {key[-1]} output {'on' if value else 'off'}.")
    if key.startswith("cyl_"):
        return (f"Cilindro {key[-1].upper()} {'avançado' if value else 'recolhido'}." if pt else
                f"Cylinder {key[-1].upper()} {'extended' if value else 'retracted'}.")
    if key in {"light_green", "light_red"}:
        color = ("verde" if key == "light_green" else "vermelha") if pt else key[6:]
        return (f"Saída da luz {color} {'ligada' if value else 'desligada'}." if pt else
                f"{color.capitalize()} light output {'on' if value else 'off'}.")
    if key in {"robot_metal", "robot_nonmetal"}:
        number = 2 if key == "robot_metal" else 3
        return (f"Pedido de recolha {'ativo' if value else 'inativo'} no tapete {number}." if pt else
                f"Pickup request {'active' if value else 'inactive'} on conveyor {number}.")
    return "Estado atualizado." if pt else "State updated."


def operator_message(event: dict, lang: str, fallback: str = "") -> str:
    pt = lang == "pt"
    command, reason = str(event.get("command") or ""), event.get("reason")
    if reason in {"queued", "written"}:
        return pending_message(command, lang)
    if reason == "system_error":
        return _state_message("system_error", 1, lang)
    if command == "PLC_STATE" and event.get("plc_value") is not None:
        return _state_message(event.get("plc_key", ""), event["plc_value"], lang)
    target = command_target(command)
    if reason == "state_observed" and target is not None:
        return _state_message(*target, lang)
    action = command_label(command, lang)
    if reason in {"timeout", "feedback_lost", "no_fresh_transition"}:
        return f"Sem confirmação: {action}." if pt else f"No confirmation: {action}."
    if reason in {"write_error", "disconnected", "endpoint_changed", "stale_or_endpoint_changed", "opcua_unavailable"}:
        return f"Envio não concluído: {action}." if pt else f"Send not completed: {action}."
    if reason == "reset_error":
        return f"Falha ao terminar o envio: {action}." if pt else f"Failed to finish sending: {action}."
    if reason in {"superseded", "superseded_by_stop"}:
        return f"Pedido substituído: {action}." if pt else f"Request superseded: {action}."
    return fallback


def summarize_events(events: list[dict]) -> list[dict]:
    confirmed = {event.get("request_id") for event in events
                 if event.get("reason") == "state_observed" and event.get("request_id") is not None}
    rows = []
    request_rows = {}
    for event in events:
        request_id, reason = event.get("request_id"), event.get("reason")
        if reason == "state_change":
            if request_id not in confirmed:
                rows.append(event)
            continue
        if request_id is None:
            rows.append(event)
        elif request_id not in request_rows:
            request_rows[request_id] = len(rows)
            rows.append(event)
        else:
            index = request_rows[request_id]
            first = rows[index]
            rows[index] = {**event, "id": first["id"], "time": first["time"], "source": first["source"]}
    return rows
