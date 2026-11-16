"""Speech wording that distinguishes acceptance from physical PLC confirmation."""

from blanky.command_messages import command_label


def command_group_key(command: str) -> str:
    parts = command.split("_")
    if command in {"START", "STOP"}:
        return "system"
    if command.startswith("MODE_"):
        return "mode"
    if command.startswith("MOTOR_") and len(parts) >= 2:
        return "motor_" + parts[1]
    if command.startswith("CYL_") and len(parts) >= 2:
        return "cyl_" + parts[1]
    if command.startswith("ROBOT_"):
        return "robot"
    if command.startswith("GREEN_"):
        return "light_green"
    if command.startswith("RED_"):
        return "light_red"
    return command


def operational_speech(command: str, accepted: bool, detail: str, lang: str) -> str:
    if not accepted:
        return detail
    label = command_label(command, lang)
    if command in {"MODE_FAST", "MODE_IDEAL", "MODE_MANUAL"}:
        label = ("selecionar o " if lang == "pt" else "select ") + label
    return (f"Pedido para {label} aceite." if lang == "pt" else
            f"Request to {label} accepted.")
