"""User-facing rejection messages shared by events, the interface and speech."""

import re


REJECTION_TEXT = {
    "pt": {
        "before_start": "Primeiro, inicie o sistema.",
        "choose_mode": "Escolha primeiro um modo: rápido, ideal ou manual.",
        "manual_only": "Os componentes só se comandam no modo manual. Mude primeiro de modo.",
        "change_mode_first": 'Para trocar de modo, use primeiro "Mudar de modo".',
        "choose_new_mode": "Escolha o novo modo: rápido, ideal ou manual.",
        "unknown": "Não percebi. Podes repetir?",
        "no_audio": "Não ouvi nada. Tente outra vez.",
        "feedback_unavailable": "Não consigo confirmar o estado do PLC. Verifica a comunicação antes de comandar.",
        "command_pending": "Já existe um pedido pendente para este controlo. Aguarda a confirmação.",
        "opcua_unavailable": "Não foi possível colocar o pedido na fila OPC UA.",
        "cylinder_retract_unavailable": "O recuo deste cilindro não está disponível através do Blanky nesta versão. Podes utilizar a HMI.",
        "system_error": "O PLC comunica um erro. Não posso enviar este comando.",
    },
    "en": {
        "before_start": "First, start the system.",
        "choose_mode": "First, choose a mode: fast, ideal or manual.",
        "manual_only": "Components can only be controlled in manual mode. Change mode first.",
        "change_mode_first": 'To switch modes, first use "Change mode".',
        "choose_new_mode": "Choose the new mode: fast, ideal or manual.",
        "unknown": "I didn't understand. Can you repeat?",
        "no_audio": "I did not hear anything. Please try again.",
        "feedback_unavailable": "I cannot confirm the PLC state. Check the connection before sending a command.",
        "command_pending": "A request for this control is still pending. Wait for confirmation.",
        "opcua_unavailable": "The request could not be queued for OPC UA.",
        "cylinder_retract_unavailable": "Retracting this cylinder is not available through Blanky in this version. You can use the HMI.",
        "system_error": "The PLC reports an error. I cannot send this command.",
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
        "ROBOT_TO_METAL": "Já existe um pedido de recolha no Tapete 2.",
        "ROBOT_TO_NONMETAL": "Já existe um pedido de recolha no Tapete 3.",
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
        "ROBOT_TO_METAL": "A pickup request is already active on Conveyor 2.",
        "ROBOT_TO_NONMETAL": "A pickup request is already active on Conveyor 3.",
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


def command_label(command: str, lang: str) -> str:
    """A short spoken name for an event, never its internal identifier."""
    pt = {
        "START": "iniciar o sistema", "STOP": "parar o sistema",
        "MODE_FAST": "modo rápido", "MODE_IDEAL": "modo ideal", "MODE_MANUAL": "modo manual",
        "MODE_UNSPEC": "mudar de modo", "GREEN_ON": "acender a luz verde",
        "GREEN_OFF": "apagar a luz verde", "RED_ON": "acender a luz vermelha",
        "RED_OFF": "apagar a luz vermelha", "ROBOT_TO_METAL": "recolha no Tapete 2",
        "ROBOT_TO_NONMETAL": "recolha no Tapete 3", "UNKNOWN": "pedido não reconhecido",
        "NO_AUDIO": "pedido sem áudio", "SYSTEM_RESET": "reiniciar o sistema",
        "SYSTEM_SHUTDOWN": "desligar o Blanky", "SET_SETTING": "alterar uma definição",
        "QUERY_SETTING": "consultar uma definição", "QUERY_CLARIFY": "esclarecer uma definição",
    }
    en = {
        "START": "start the system", "STOP": "stop the system",
        "MODE_FAST": "fast mode", "MODE_IDEAL": "ideal mode", "MODE_MANUAL": "manual mode",
        "MODE_UNSPEC": "change mode", "GREEN_ON": "turn on the green light",
        "GREEN_OFF": "turn off the green light", "RED_ON": "turn on the red light",
        "RED_OFF": "turn off the red light", "ROBOT_TO_METAL": "pickup on Conveyor 2",
        "ROBOT_TO_NONMETAL": "pickup on Conveyor 3", "UNKNOWN": "unrecognized request",
        "NO_AUDIO": "request without audio", "SYSTEM_RESET": "reset the system",
        "SYSTEM_SHUTDOWN": "shut down Blanky", "SET_SETTING": "change a setting",
        "QUERY_SETTING": "ask about a setting", "QUERY_CLARIFY": "clarify a setting",
    }
    fixed = pt if lang == "pt" else en
    if command in fixed:
        return fixed[command]
    motor = re.fullmatch(r"MOTOR_([123])_(ON|OFF)", command)
    if motor:
        number, action = motor.groups()
        return (f"{'ligar' if action == 'ON' else 'desligar'} o motor {number}" if lang == "pt"
                else f"turn {'on' if action == 'ON' else 'off'} motor {number}")
    cylinder = re.fullmatch(r"CYL_([ABCD])_(EXTEND|RETRACT)", command)
    if cylinder:
        letter, action = cylinder.groups()
        return (f"{'avançar' if action == 'EXTEND' else 'recuar'} o cilindro {letter}" if lang == "pt"
                else f"{'extend' if action == 'EXTEND' else 'retract'} cylinder {letter}")
    return "consulta" if lang == "pt" else "query"


def plc_observation_message(command: str, lang: str) -> str:
    """Describe an observed return after a request without claiming causality."""
    fixed = {
        "START": ("O PLC comunica o sistema ligado.", "The PLC reports the system on."),
        "STOP": ("O PLC comunica o sistema parado.", "The PLC reports the system stopped."),
        "MODE_FAST": ("O PLC comunica o modo rápido ativo.", "The PLC reports fast mode active."),
        "MODE_IDEAL": ("O PLC comunica o modo ideal ativo.", "The PLC reports ideal mode active."),
        "MODE_MANUAL": ("O PLC comunica o modo manual ativo.", "The PLC reports manual mode active."),
        "MODE_UNSPEC": ("O PLC comunica mudança de modo.", "The PLC reports mode change."),
        "GREEN_ON": ("A saída lógica da luz verde está ligada.", "The green light's logical output is on."),
        "GREEN_OFF": ("A saída lógica da luz verde está desligada.", "The green light's logical output is off."),
        "RED_ON": ("A saída lógica da luz vermelha está ligada.", "The red light's logical output is on."),
        "RED_OFF": ("A saída lógica da luz vermelha está desligada.", "The red light's logical output is off."),
        "ROBOT_TO_METAL": ("O PLC comunica pedido de recolha no Tapete 2, não execução do robô.",
                           "The PLC reports a pickup request on Conveyor 2, not robot execution."),
        "ROBOT_TO_NONMETAL": ("O PLC comunica pedido de recolha no Tapete 3, não execução do robô.",
                              "The PLC reports a pickup request on Conveyor 3, not robot execution."),
    }
    if command in fixed:
        return fixed[command][0 if lang == "pt" else 1]
    motor = re.fullmatch(r"MOTOR_([123])_(ON|OFF)", command)
    if motor:
        number, action = motor.groups()
        return (f"A saída lógica do motor {number} está {'ligada' if action == 'ON' else 'desligada'}."
                if lang == "pt" else f"Motor {number}'s logical output is {'on' if action == 'ON' else 'off'}.")
    cylinder = re.fullmatch(r"CYL_([ABCD])_(EXTEND|RETRACT)", command)
    if cylinder:
        letter, action = cylinder.groups()
        return (f"O sensor comunica o cilindro {letter} {'avançado' if action == 'EXTEND' else 'recolhido'}."
                if lang == "pt" else f"The sensor reports cylinder {letter} {'extended' if action == 'EXTEND' else 'retracted'}.")
    return "Estado comunicado pelo PLC." if lang == "pt" else "State reported by the PLC."


def plc_change_message(key: str, value: int, lang: str) -> str:
    if key == "system_error" and value:
        return "O PLC comunica um erro ativo." if lang == "pt" else "The PLC reports an active error."
    if key == "start":
        return ("O PLC comunica o sistema ligado." if value else "O PLC comunica o sistema parado.") if lang == "pt" else (
            "The PLC reports the system on." if value else "The PLC reports the system stopped.")
    modes = {
        "mode_fast": ("rápido", "fast"), "mode_ideal": ("ideal", "ideal"),
        "mode_manual": ("manual", "manual"), "mode_change": ("de mudança", "change"),
    }
    if key in modes:
        mode = modes[key][0 if lang == "pt" else 1]
        return (f"O PLC comunica o modo {mode} {'ativo' if value else 'inativo'}." if lang == "pt" else
                f"The PLC reports {mode} mode {'active' if value else 'inactive'}.")
    if key in {"robot_metal", "robot_nonmetal"}:
        conveyor = 2 if key == "robot_metal" else 3
        return (f"Pedido de recolha no Tapete {conveyor} {'ativo' if value else 'inativo'}, comunicado pelo PLC."
                if lang == "pt" else f"Pickup request on Conveyor {conveyor} {'active' if value else 'inactive'}, reported by the PLC.")
    label = key.replace("_", " ")
    return (f"Alteração recebida do PLC: {label} {'ativo' if value else 'inativo'}."
            if lang == "pt" else f"PLC-reported change: {label} {'active' if value else 'inactive'}.")
