"""User-facing rejection messages shared by events, the interface and speech."""

import re


REJECTION_TEXT = {
    "pt": {
        "before_start": "Primeiro, inicie o sistema.",
        "choose_mode": "Escolha primeiro um modo: rápido, ideal ou manual.",
        "manual_only": "Os componentes só se comandam no modo manual. Mude primeiro de modo.",
        "change_mode_first": 'Para trocar de modo, use primeiro "Mudar de modo".',
        "choose_new_mode": "Escolha o novo modo: rápido, ideal ou manual.",
        "unknown": "Não percebi o pedido. Pode repetir?",
        "no_audio": "Não ouvi nada. Tente outra vez.",
    },
    "en": {
        "before_start": "First, start the system.",
        "choose_mode": "First, choose a mode: fast, ideal or manual.",
        "manual_only": "Components can only be controlled in manual mode. Change mode first.",
        "change_mode_first": 'To switch modes, first use "Change mode".',
        "choose_new_mode": "Choose the new mode: fast, ideal or manual.",
        "unknown": "I did not understand the request. Could you repeat it?",
        "no_audio": "I did not hear anything. Please try again.",
    },
}

_NO_CHANGE = {
    "pt": {
        "START": "O sistema já está iniciado.",
        "STOP": "O sistema já está parado.",
        "MODE_FAST": "O modo rápido já está ativo.",
        "MODE_IDEAL": "O modo ideal já está ativo.",
        "MODE_MANUAL": "O modo manual já está ativo.",
        "MODE_UNSPEC": "A troca de modo já está ativa.",
        "GREEN_ON": "A luz verde já está acesa.",
        "GREEN_OFF": "A luz verde já está apagada.",
        "RED_ON": "A luz vermelha já está acesa.",
        "RED_OFF": "A luz vermelha já está apagada.",
        "ROBOT_TO_METAL": "O robô já está nas peças metálicas.",
        "ROBOT_TO_NONMETAL": "O robô já está nas peças não metálicas.",
    },
    "en": {
        "START": "The system is already started.",
        "STOP": "The system is already stopped.",
        "MODE_FAST": "Fast mode is already active.",
        "MODE_IDEAL": "Ideal mode is already active.",
        "MODE_MANUAL": "Manual mode is already active.",
        "MODE_UNSPEC": "Mode change is already active.",
        "GREEN_ON": "The green light is already on.",
        "GREEN_OFF": "The green light is already off.",
        "RED_ON": "The red light is already on.",
        "RED_OFF": "The red light is already off.",
        "ROBOT_TO_METAL": "The robot is already at the metal pieces.",
        "ROBOT_TO_NONMETAL": "The robot is already at the non-metal pieces.",
    },
}


def no_change_message(command: str, lang: str) -> str:
    language = "pt" if lang == "pt" else "en"
    fixed = _NO_CHANGE[language].get(command)
    if fixed:
        return fixed

    motor = re.fullmatch(r"MOTOR_([123])_(ON|OFF)", command)
    if motor:
        number, action = motor.groups()
        if language == "pt":
            return f"O motor {number} já está {'ligado' if action == 'ON' else 'desligado'}."
        return f"Motor {number} is already {'on' if action == 'ON' else 'off'}."

    cylinder = re.fullmatch(r"CYL_([ABCD])_(EXTEND|RETRACT)", command)
    if cylinder:
        letter, action = cylinder.groups()
        if language == "pt":
            return f"O cilindro {letter} já está {'avançado' if action == 'EXTEND' else 'recolhido'}."
        return f"Cylinder {letter} is already {'extended' if action == 'EXTEND' else 'retracted'}."

    return "Este pedido não altera o estado." if language == "pt" else "This request does not change the state."


def rejection_message(reason: str, lang: str, command: str = "") -> str:
    if reason == "no_change":
        return no_change_message(command, lang)
    language = "pt" if lang == "pt" else "en"
    return REJECTION_TEXT[language].get(reason, REJECTION_TEXT[language]["unknown"])


def rejection_for_event(event: dict, lang: str) -> str:
    return rejection_message(str(event.get("reason") or "unknown"), lang, str(event.get("command") or ""))
