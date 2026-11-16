"""Short, read-only status answers for speech and text interaction."""

from blanky.opcua_nodes import COMMAND_TO_RECEIVE_SIGNAL
from blanky.command_messages import command_label


def _say(lang: str, pt: str, en: str) -> str:
    return pt if lang == "pt" else en


def _mode(state: dict, lang: str) -> str:
    for key, pt, en in (("mode_fast", "rápido", "fast"), ("mode_ideal", "ideal", "ideal"),
                        ("mode_manual", "manual", "manual"), ("mode_change", "em mudança", "being changed")):
        if state.get(key):
            return _say(lang, pt, en)
    return _say(lang, "ainda não escolhido", "not selected yet")


def _component(component: str, state: dict, health: dict, lang: str) -> str:
    if component == "lights":
        green = _say(lang, "acesa" if state.get("light_green") else "apagada",
                     "on" if state.get("light_green") else "off")
        red = _say(lang, "acesa" if state.get("light_red") else "apagada",
                   "on" if state.get("light_red") else "off")
        return _say(lang, f"No Blanky, a luz verde está {green} e a vermelha está {red}. Não são estados físicos confirmados.",
                    f"In Blanky, the green light is {green} and the red light is {red}. These are not confirmed physical states.")
    if component.startswith("motor_"):
        number = component[-1]
        label = f"Motor {number}"
        active = bool(state.get(component))
        action = f"MOTOR_{number}_{'ON' if active else 'OFF'}"
        status = _say(lang, "ligado" if active else "desligado", "on" if active else "off")
    elif component.startswith("cyl_"):
        letter = component[-1].upper()
        label = _say(lang, f"Cilindro {letter}", f"Cylinder {letter}")
        active = bool(state.get(component))
        action = f"CYL_{letter}_{'EXTEND' if active else 'RETRACT'}"
        status = _say(lang, "com avanço solicitado" if active else "sem avanço solicitado",
                      "with extend requested" if active else "without extend requested")
    elif component.startswith("light_"):
        color = component.removeprefix("light_")
        label = _say(lang, "Luz verde" if color == "green" else "Luz vermelha",
                     "Green light" if color == "green" else "Red light")
        active = bool(state.get(component))
        action = ("GREEN" if color == "green" else "RED") + ("_ON" if active else "_OFF")
        status = _say(lang, "acesa" if active else "apagada", "on" if active else "off")
    else:
        metal = bool(state.get("robot_metal"))
        nonmetal = bool(state.get("robot_nonmetal"))
        label = _say(lang, "Robô", "Robot")
        action = "ROBOT_TO_METAL" if metal else "ROBOT_TO_NONMETAL" if nonmetal else ""
        status = _say(lang, "com destino peças metálicas" if metal else "com destino peças não metálicas" if nonmetal else "sem destino ativo",
                      "targeting metal pieces" if metal else "targeting non-metal pieces" if nonmetal else "with no active target")

    article = "a" if component.startswith("light_") else "o"
    base = _say(lang, f"Segundo o Blanky, {article} {label.lower()} está {status}.",
                f"According to Blanky, {label.lower()} is {status}.")
    signal = COMMAND_TO_RECEIVE_SIGNAL.get(action)
    received = health.get("opcua_received") or {}
    if signal and health.get("opcua_feedback_active") and received.get(signal):
        return base + _say(lang, " Sinal de comando confirmado pelo PLC; a posição física não está confirmada.",
                           " Command signal confirmed by the PLC; physical position is not confirmed.")
    return base + _say(lang, " É o estado interno do Blanky, não uma posição física confirmada.",
                       " This is Blanky's internal state, not a confirmed physical position.")


def answer_query(name: str, component: str, lang: str, state: dict, health: dict,
                 events: list[dict], allowed: set[str], last_response: str) -> str:
    """Build an answer from snapshots only; never writes to the PLC or MQTT state."""
    if name == "REPEAT":
        return last_response or _say(lang, "Ainda não tenho uma resposta para repetir.", "There is no answer to repeat yet.")
    if name == "QUERY_SYSTEM":
        status = (_say(lang, f"O sistema está iniciado. Modo {_mode(state, lang)}.",
                       f"The system is started. Mode: {_mode(state, lang)}.") if state.get("start")
                  else _say(lang, "O sistema está parado, sem modo ativo.", "The system is stopped, with no active mode."))
        if (health.get("opcua_received") or {}).get("system_error") and health.get("opcua_feedback_active"):
            status += _say(lang, " O PLC comunica um erro ativo.", " The PLC reports an active error.")
        return status
    if name == "QUERY_MODE":
        if not state.get("start"):
            return _say(lang, "O sistema está parado, sem modo ativo.", "The system is stopped, with no active mode.")
        if not any(state.get(key) for key in ("mode_fast", "mode_ideal", "mode_manual", "mode_change")):
            return _say(lang, "Ainda não escolheste um modo.", "You have not chosen a mode yet.")
        return _say(lang, f"O modo está {_mode(state, lang)}.", f"The mode is {_mode(state, lang)}.")
    if name == "QUERY_COMPONENT":
        return _component(component, state, health, lang)
    if name == "QUERY_MQTT":
        return _say(lang, "O MQTT está ligado." if health.get("mqtt_base_connected") else "O MQTT está desligado. O telemóvel não comunica com o Blanky.",
                    "MQTT is connected." if health.get("mqtt_base_connected") else "MQTT is disconnected. The phone cannot communicate with Blanky.")
    if name == "QUERY_OPCUA":
        return _say(lang, "O OPC UA está ligado ao PLC." if health.get("opcua_connected") else "O OPC UA está desligado. Os comandos não chegam à maquete.",
                    "OPC UA is connected to the PLC." if health.get("opcua_connected") else "OPC UA is disconnected. Commands do not reach the machine.")
    if name == "QUERY_OPENAI":
        if not health.get("openai_configured"):
            return _say(lang, "A OpenAI não está configurada. A interpretação Online não está disponível.",
                        "OpenAI is not configured. Online interpretation is unavailable.")
        last = (health.get("openai_activity") or {}).get("last")
        if last and not last.get("ok"):
            return _say(lang, "A chave OpenAI está configurada, mas o último pedido falhou.",
                        "The OpenAI key is configured, but the last request failed.")
        if last and last.get("ok"):
            return _say(lang, "A chave OpenAI está configurada e o último pedido respondeu. Isso não garante a ligação neste momento.",
                        "The OpenAI key is configured and the last request succeeded. This does not guarantee a connection now.")
        return _say(lang, "A chave OpenAI está configurada; a disponibilidade só é confirmada quando um pedido responde.",
                    "The OpenAI key is configured; availability is only confirmed by a successful request.")
    if name == "QUERY_CONNECTIONS":
        mqtt = _say(lang, "ligado" if health.get("mqtt_base_connected") else "desligado",
                    "connected" if health.get("mqtt_base_connected") else "disconnected")
        opcua = _say(lang, "ligado" if health.get("opcua_connected") else "desligado",
                     "connected" if health.get("opcua_connected") else "disconnected")
        ai = _say(lang, "configurada" if health.get("openai_configured") else "não configurada",
                  "configured" if health.get("openai_configured") else "not configured")
        summary = _say(lang, f"MQTT {mqtt}; OPC UA {opcua}; OpenAI {ai}.",
                       f"MQTT {mqtt}; OPC UA {opcua}; OpenAI {ai}.")
        consequences = []
        if not health.get("mqtt_base_connected"):
            consequences.append(_say(lang, "telemóvel sem comunicação", "phone communication unavailable"))
        if not health.get("opcua_connected"):
            consequences.append(_say(lang, "comandos sem chegar à maquete", "commands cannot reach the machine"))
        if not health.get("openai_configured"):
            consequences.append(_say(lang, "interpretação Online indisponível", "Online interpretation unavailable"))
        if consequences:
            summary += " " + _say(lang, "Consequência: ", "Impact: ") + "; ".join(consequences) + "."
        return summary
    if name == "QUERY_ERRORS":
        if not health.get("opcua_feedback_active"):
            return _say(lang, "Não consigo confirmar erros no PLC: o retorno OPC UA está indisponível.",
                        "I cannot confirm PLC errors: OPC UA feedback is unavailable.")
        return _say(lang, "O PLC comunica um erro ativo, mas não fornece a causa neste sinal." if (health.get("opcua_received") or {}).get("system_error")
                    else "O PLC não comunica um erro ativo.",
                    "The PLC reports an active error, but this signal does not include the cause." if (health.get("opcua_received") or {}).get("system_error")
                    else "The PLC reports no active error.")
    if name == "QUERY_LAST_EVENT":
        if not events:
            return _say(lang, "Ainda não há eventos.", "There are no events yet.")
        event = events[-1]
        source = {"voice": ("voz", "voice"), "text": ("Text-Bot", "Text-Bot"),
                  "mqtt_text": ("telemóvel", "phone"), "mqtt_panel": ("telemóvel", "phone"),
                  "button": ("botão", "button")}.get(event.get("source"), ("sistema", "system"))
        result = _say(lang, "aceite" if event.get("accepted") else "recusado",
                      "accepted" if event.get("accepted") else "rejected")
        detail = "" if event.get("kind") == "query" else (event.get(f"detail_{lang}") or event.get("detail") or "")
        action = command_label(str(event.get("command") or ""), lang)
        return _say(lang, f"Último evento por {source[0]}: {action}, {result}. {detail}".strip(),
                    f"Last event from {source[1]}: {action}, {result}. {detail}".strip())
    if name == "QUERY_OPTIONS":
        if "START" in allowed and not state.get("start"):
            return _say(lang, "Podes iniciar o sistema ou consultar o seu estado.",
                        "You can start the system or ask for its status.")
        if "MODE_FAST" in allowed and not any(state.get(key) for key in ("mode_fast", "mode_ideal", "mode_manual")):
            return _say(lang, "Podes escolher o modo rápido, ideal ou manual, ou parar o sistema.",
                        "You can choose fast, ideal or manual mode, or stop the system.")
        if "MOTOR_1_ON" in allowed:
            return _say(lang, "Podes comandar motores, cilindros, luzes e robô, mudar de modo ou parar.",
                        "You can control motors, cylinders, lights and the robot, change mode or stop.")
        return _say(lang, "Podes mudar de modo ou parar o sistema.", "You can change mode or stop the system.")
    return _say(lang, "Não percebi a consulta.", "I did not understand the question.")
