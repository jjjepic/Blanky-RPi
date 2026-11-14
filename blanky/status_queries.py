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


def _group_parts(target: str, value: str, lang: str, state: dict, health: dict | None = None) -> dict[str, str]:
    groups = {
        "motors": [(f"motor_{n}", f"motor {n}") for n in (1, 2, 3)],
        "cylinders": [(f"cyl_{letter.lower()}", _say(lang, f"cilindro {letter}", f"cylinder {letter}"))
                      for letter in "ABCD"],
        "lights": [("light_green", _say(lang, "luz verde", "green light")),
                   ("light_red", _say(lang, "luz vermelha", "red light"))],
        "robot": [("robot_metal", _say(lang, "robô para metal", "robot to metal")),
                  ("robot_nonmetal", _say(lang, "robô para não metal", "robot to non-metal"))],
    }
    members = [entry for group in groups.values() for entry in group] if target == "all" else groups.get(target, [])
    if value == "" and target != "all":
        if target == "robot":
            speech = (_say(lang, "Robô com destino metal.", "Robot targeting metal.") if state.get("robot_metal") else
                      _say(lang, "Robô com destino não metal.", "Robot targeting non-metal.") if state.get("robot_nonmetal") else
                      _say(lang, "Robô sem destino ativo.", "Robot has no active destination."))
        elif target == "cylinders":
            active_letters = [key[-1].upper() for key, _ in members if state.get(key)]
            inactive_letters = [key[-1].upper() for key, _ in members if not state.get(key)]
            active_text = ", ".join(active_letters)
            inactive_text = ", ".join(inactive_letters)
            speech = _say(lang, f"Avanço pedido: {active_text or 'nenhum'}; sem pedido: {inactive_text or 'nenhum'}.",
                          f"Extend requested: {active_text or 'none'}; not requested: {inactive_text or 'none'}.")
        else:
            statuses = []
            for key, label in members:
                active_label = (_say(lang, "com avanço solicitado", "extend requested") if target == "cylinders" else
                                _say(lang, "acesa", "on") if target == "lights" else _say(lang, "ligado", "on"))
                inactive_label = (_say(lang, "sem avanço solicitado", "no extend requested") if target == "cylinders" else
                                  _say(lang, "apagada", "off") if target == "lights" else _say(lang, "desligado", "off"))
                statuses.append(f"{label} {active_label if state.get(key) else inactive_label}")
            sentence = "; ".join(statuses)
            speech = sentence[:1].upper() + sentence[1:] + "."
        return {"speech": speech, "detail": speech + _say(lang,
                " Estado interno do Blanky; a posição física não está confirmada.",
                " Blanky's internal state; physical position is not confirmed.")}
    active = value not in {"off", "retracted"}
    selected = [label for key, label in members if bool(state.get(key)) == active]
    if not selected:
        speech = {
            "motors": _say(lang, "Nenhum motor está ligado." if active else "Nenhum motor está desligado.",
                           "No motor is on." if active else "No motor is off."),
            "cylinders": _say(lang, "Nenhum cilindro tem avanço solicitado." if active else "Todos os cilindros têm avanço solicitado.",
                              "No cylinder has extend requested." if active else "All cylinders have extend requested."),
            "lights": _say(lang, "Nenhuma luz está acesa." if active else "Nenhuma luz está apagada.",
                           "No light is on." if active else "No light is off."),
            "robot": _say(lang, "O robô não tem destino ativo.", "The robot has no active destination."),
            "all": _say(lang, "Nenhum componente está ativo.", "No component is active."),
        }[target]
    else:
        names = ", ".join(selected[:-1]) + (_say(lang, " e ", " and ") if len(selected) > 1 else "") + selected[-1]
        suffix = (_say(lang, "está", "is") if len(selected) == 1 else _say(lang, "estão", "are"))
        state_word = (_say(lang, "com avanço solicitado", "with extend requested") if target == "cylinders" else
                      _say(lang, "acesa", "on") if target == "lights" else _say(lang, "ligado", "on"))
        if not active:
            state_word = (_say(lang, "sem avanço solicitado", "without extend requested") if target == "cylinders" else
                          _say(lang, "apagada", "off") if target == "lights" else _say(lang, "desligado", "off"))
        if len(selected) > 1 and lang == "pt" and target == "motors":
            state_word += "s"
        if len(selected) > 1 and lang == "pt" and target == "lights":
            state_word += "s"
        if target == "all":
            speech = _say(lang, f"Componentes ativos: {names}.", f"Active components: {names}.")
        else:
            speech = f"{names[:1].upper() + names[1:]} {suffix} {state_word}."
        if target == "all" and len(selected) > 3:
            speech = _say(lang, f"{len(selected)} componentes estão ativos.",
                          f"{len(selected)} components are active.")
        if len(selected) == 1 and target == "motors" and active:
            speech = _say(lang, f"Só o {selected[0]} está ligado.", f"Only {selected[0]} is on.")
    detail = speech
    if target == "all" and len(selected) > 3:
        detail += _say(lang, f" Componentes: {', '.join(selected)}.", f" Components: {', '.join(selected)}.")
    detail += _say(lang, " Estado interno do Blanky; não confirma a posição física dos atuadores.",
                           " Blanky's internal state; actuator position is not physically confirmed.")
    if health and health.get("opcua_feedback_active"):
        received = health.get("opcua_received") or {}
        confirmed = []
        for key, label in members:
            if label not in selected:
                continue
            if key.startswith("motor_"):
                action = f"MOTOR_{key[-1]}_{'ON' if state.get(key) else 'OFF'}"
            elif key.startswith("cyl_"):
                action = f"CYL_{key[-1].upper()}_{'EXTEND' if state.get(key) else 'RETRACT'}"
            elif key.startswith("light_"):
                action = ("GREEN" if key == "light_green" else "RED") + ("_ON" if state.get(key) else "_OFF")
            else:
                action = "ROBOT_TO_METAL" if key == "robot_metal" else "ROBOT_TO_NONMETAL"
            signal = COMMAND_TO_RECEIVE_SIGNAL.get(action)
            if signal and received.get(signal):
                confirmed.append(label)
        if confirmed:
            detail += _say(lang, f" Sinal confirmado pelo PLC: {', '.join(confirmed)}.",
                           f" PLC command signal confirmed: {', '.join(confirmed)}.")
    return {"speech": speech, "detail": detail}


def answer_query_parts(name: str, target: str, value: str, lang: str, state: dict, health: dict,
                       events: list[dict], allowed: set[str], last_response: str) -> dict[str, str]:
    """Keep speech concise while retaining provenance and consequences in detail."""
    if name in {"QUERY_COMPONENT_GROUP", "QUERY_ACTIVE"}:
        return _group_parts("all" if name == "QUERY_ACTIVE" else target, value, lang, state, health)
    detail = answer_query(name, target, lang, state, health, events, allowed, last_response)
    if name == "QUERY_COMPONENT":
        if target.startswith("motor_"):
            n = target[-1]
            speech = _say(lang, f"Motor {n} {'ligado' if state.get(target) else 'desligado'}.",
                          f"Motor {n} {'on' if state.get(target) else 'off'}.")
        elif target.startswith("cyl_"):
            letter = target[-1].upper()
            speech = _say(lang, f"Cilindro {letter}: {'avanço solicitado' if state.get(target) else 'sem avanço solicitado'}.",
                          f"Cylinder {letter}: {'extend requested' if state.get(target) else 'no extend requested'}.")
        elif target == "robot":
            speech = _say(lang, "Robô para metal." if state.get("robot_metal") else "Robô para não metal." if state.get("robot_nonmetal") else "Robô sem destino ativo.",
                          "Robot to metal." if state.get("robot_metal") else "Robot to non-metal." if state.get("robot_nonmetal") else "Robot has no active destination.")
        elif target == "lights":
            speech = _group_parts("lights", "", lang, state, health)["speech"]
        else:
            color = "green" if target == "light_green" else "red"
            speech = _say(lang, f"Luz {'verde' if color == 'green' else 'vermelha'} {'acesa' if state.get(target) else 'apagada'}.",
                          f"{'Green' if color == 'green' else 'Red'} light {'on' if state.get(target) else 'off'}.")
    elif name == "QUERY_MQTT":
        speech = _say(lang, "MQTT ligado." if health.get("mqtt_base_connected") else "MQTT desligado.",
                      "MQTT connected." if health.get("mqtt_base_connected") else "MQTT disconnected.")
    elif name == "QUERY_OPCUA":
        speech = _say(lang, "OPC UA ligado." if health.get("opcua_connected") else "OPC UA desligado.",
                      "OPC UA connected." if health.get("opcua_connected") else "OPC UA disconnected.")
    elif name == "QUERY_OPENAI":
        speech = _say(lang, "OpenAI configurada." if health.get("openai_configured") else "OpenAI indisponível.",
                      "OpenAI configured." if health.get("openai_configured") else "OpenAI unavailable.")
    elif name == "QUERY_CONNECTIONS":
        speech = _say(lang,
                      f"MQTT {'ligado' if health.get('mqtt_base_connected') else 'desligado'}; OPC UA {'ligado' if health.get('opcua_connected') else 'desligado'}; OpenAI {'configurada' if health.get('openai_configured') else 'indisponível'}.",
                      f"MQTT {'connected' if health.get('mqtt_base_connected') else 'disconnected'}; OPC UA {'connected' if health.get('opcua_connected') else 'disconnected'}; OpenAI {'configured' if health.get('openai_configured') else 'unavailable'}.")
    elif name == "QUERY_ERRORS":
        error = (health.get("opcua_received") or {}).get("system_error")
        speech = _say(lang, "O PLC comunica um erro." if error else "O PLC não comunica erros." if health.get("opcua_feedback_active") else "Não consigo confirmar erros no PLC.",
                      "The PLC reports an error." if error else "The PLC reports no errors." if health.get("opcua_feedback_active") else "I cannot confirm PLC errors.")
    elif name == "QUERY_SYSTEM":
        speech = _say(lang, f"Sistema iniciado. Modo {_mode(state, lang)}." if state.get("start") else "Sistema parado.",
                      f"System started. Mode {_mode(state, lang)}." if state.get("start") else "System stopped.")
        if (health.get("opcua_received") or {}).get("system_error") and health.get("opcua_feedback_active"):
            speech += _say(lang, " Erro comunicado pelo PLC.", " PLC reports an error.")
    elif name == "QUERY_LAST_EVENT":
        speech = detail.split(". ")[0] + "." if ". " in detail else detail
    elif name == "QUERY_OPTIONS":
        speech = (_say(lang, "Podes iniciar o sistema.", "You can start the system.")
                  if not state.get("start") else
                  _say(lang, "Escolhe um modo ou para o sistema.", "Choose a mode or stop the system.")
                  if not any(state.get(key) for key in ("mode_fast", "mode_ideal", "mode_manual")) else
                  _say(lang, "Podes comandar componentes, mudar de modo ou parar.",
                       "You can control components, change mode or stop.")
                  if "MOTOR_1_ON" in allowed else
                  _say(lang, "Podes mudar de modo ou parar.", "You can change mode or stop."))
    else:
        speech = detail
    return {"speech": speech, "detail": detail}


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
    if name in {"QUERY_COMPONENT_GROUP", "QUERY_ACTIVE"}:
        return _group_parts("all" if name == "QUERY_ACTIVE" else component, "", lang, state, health)["detail"]
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
