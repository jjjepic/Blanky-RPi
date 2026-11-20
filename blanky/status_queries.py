"""Short, read-only status answers for speech and text interaction."""

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
        return _group_parts("lights", "", lang, state, health)["detail"]
    if component == "robot":
        return _group_parts("robot", "", lang, state, health)["detail"]
    value = state.get(component)
    if component.startswith("motor_"):
        label = _say(lang, f"A saída lógica do motor {component[-1]}", f"The logical output for motor {component[-1]}")
        on, off = _say(lang, "ligada", "on"), _say(lang, "desligada", "off")
    elif component.startswith("cyl_"):
        letter = component[-1].upper()
        label = _say(lang, f"O cilindro {letter}", f"Cylinder {letter}")
        on, off = _say(lang, "avançado, segundo o sensor", "extended according to its sensor"), _say(lang, "recolhido, segundo o sensor", "retracted according to its sensor")
        if health.get("control_mode") == "test":
            on, off = _say(lang, "avançado", "extended"), _say(lang, "recolhido", "retracted")
    else:
        color = component.removeprefix("light_")
        label = _say(lang, f"A saída lógica da luz {'verde' if color == 'green' else 'vermelha'}",
                     f"The logical output for the {'green' if color == 'green' else 'red'} light")
        on, off = _say(lang, "ligada", "on"), _say(lang, "desligada", "off")
    if value is None:
        if component in {"cyl_c", "cyl_d"} and health.get("opcua_feedback_active"):
            return _say(lang, f"{label} não tem avanço confirmado. Não consigo confirmar o recuo.",
                        f"{label} has no confirmed extension. I cannot confirm retraction.")
        return _say(lang, f"Não consigo confirmar o estado atual de {label.lower()}.",
                    f"I cannot confirm the current state of {label.lower()}.")
    return f"{label} {'encontra-se' if lang == 'pt' else 'is'} {on if value else off}."


def _group_parts(target: str, value: str, lang: str, state: dict, health: dict | None = None) -> dict[str, str]:
    groups = {
        "motors": [f"motor_{n}" for n in (1, 2, 3)],
        "cylinders": [f"cyl_{letter}" for letter in "abcd"],
        "lights": ["light_green", "light_red"],
        "robot": ["robot_metal", "robot_nonmetal"],
    }
    keys = [key for members in groups.values() for key in members] if target == "all" else groups.get(target, [])
    if not keys:
        message = _say(lang, "Não percebi o grupo.", "I did not understand the group.")
        return {"speech": message, "detail": message}
    if target == "robot":
        if any(state.get(key) is None for key in keys):
            message = _say(lang, "Não consigo confirmar os pedidos de recolha.", "I cannot confirm the pickup requests.")
        elif health and health.get("control_mode") == "test":
            message = _say(lang, "Pedidos locais de recolha: " + ("metal e não metal" if state[keys[0]] and state[keys[1]] else "metal" if state[keys[0]] else "não metal" if state[keys[1]] else "nenhum") + ".",
                           "Local pickup requests: " + ("metal and non-metal" if state[keys[0]] and state[keys[1]] else "metal" if state[keys[0]] else "non-metal" if state[keys[1]] else "none") + ".")
        elif state["robot_metal"] and state["robot_nonmetal"]:
            message = _say(lang, "O PLC pede recolha manual nos Tapetes 2 e 3. Não há robô físico em operação.",
                           "The PLC requests manual pickup on Conveyors 2 and 3. No physical robot is operating.")
        elif state["robot_metal"]:
            message = _say(lang, "O PLC pede recolha manual no Tapete 2. Não há robô físico em operação.",
                           "The PLC requests manual pickup on Conveyor 2. No physical robot is operating.")
        elif state["robot_nonmetal"]:
            message = _say(lang, "O PLC pede recolha manual no Tapete 3. Não há robô físico em operação.",
                           "The PLC requests manual pickup on Conveyor 3. No physical robot is operating.")
        else:
            message = _say(lang, "Não há pedido de recolha ativo.", "There is no active pickup request.")
        return {"speech": message, "detail": message}
    if value:
        expected = value not in {"off", "retracted"}
        keys = [key for key in keys if state.get(key) is not None and bool(state[key]) == expected]
    parts = []
    for key in keys:
        if key.startswith("cyl_"):
            label = _say(lang, f"cilindro {key[-1].upper()}", f"cylinder {key[-1].upper()}")
        elif key.startswith("light_"):
            label = _say(lang, f"luz {'verde' if key == 'light_green' else 'vermelha'}",
                         f"{'green' if key == 'light_green' else 'red'} light")
        else:
            label = key.replace("_", " ")
        if key.startswith("cyl_") and key in {"cyl_c", "cyl_d"} and state.get(key) is None:
            parts.append(_say(lang, f"{label}: recuo não confirmado", f"{label}: retraction unconfirmed"))
        elif state.get(key) is None:
            parts.append(_say(lang, f"{label}: estado não confirmado", f"{label}: state unconfirmed"))
        else:
            if key.startswith("cyl_"):
                status = _say(lang, "avançado" if state[key] else "recolhido", "extended" if state[key] else "retracted")
            elif key.startswith("light_"):
                status = _say(lang, "acesa" if state[key] else "apagada", "on" if state[key] else "off")
            else:
                status = _say(lang, "saída ligada" if state[key] else "saída desligada",
                              "output on" if state[key] else "output off")
            parts.append(f"{label}: {status}")
    message = "; ".join(parts) + "." if parts else _say(
        lang, "Nenhum estado local corresponde à pergunta." if health and health.get("control_mode") == "test" else "Nenhum estado confirmado corresponde à pergunta.",
        "No local state matches the question." if health and health.get("control_mode") == "test" else "No confirmed state matches the question.")
    if target == "all" and len(parts) > 4:
        active = sum(state.get(key) == 1 for key in keys)
        unknown = sum(state.get(key) is None for key in keys)
        speech = _say(lang, f"Há {active} estados ativos e {unknown} sem confirmação.",
                      f"There are {active} active states and {unknown} unconfirmed states.")
    else:
        speech = message
    return {"speech": speech, "detail": message}


def answer_query_parts(name: str, target: str, value: str, lang: str, state: dict, health: dict,
                       events: list[dict], allowed: set[str], last_response: str) -> dict[str, str]:
    if name in {"QUERY_COMPONENT_GROUP", "QUERY_ACTIVE"}:
        answer = _group_parts("all" if name == "QUERY_ACTIVE" else target, value, lang, state, health)
    else:
        detail = answer_query(name, target, lang, state, health, events, allowed, last_response)
        answer = {"speech": detail, "detail": detail}
    if health.get("control_mode") == "test" and name in {
        "QUERY_SYSTEM", "QUERY_MODE", "QUERY_COMPONENT", "QUERY_COMPONENT_GROUP", "QUERY_ACTIVE", "QUERY_OPTIONS"
    }:
        prefix = _say(lang, "Em teste, estado local do Blanky: ", "In test mode, Blanky's local state: ")
        return {part: prefix + content for part, content in answer.items()}
    return answer


def answer_query(name: str, component: str, lang: str, state: dict, health: dict,
                 events: list[dict], allowed: set[str], last_response: str) -> str:
    """Build an answer from snapshots only; never writes to the PLC or MQTT state."""
    if name == "REPEAT":
        return last_response or _say(lang, "Ainda não tenho uma resposta para repetir.", "There is no answer to repeat yet.")
    if name == "QUERY_SYSTEM":
        if state.get("start") is None:
            return _say(lang, "Não consigo confirmar o estado atual do sistema.",
                        "I cannot confirm the current system state.")
        status = (_say(lang, f"O sistema está iniciado. Modo {_mode(state, lang)}.",
                       f"The system is started. Mode: {_mode(state, lang)}.") if state.get("start")
                  else _say(lang, "O sistema está parado, sem modo ativo.", "The system is stopped, with no active mode."))
        if (health.get("opcua_received") or {}).get("system_error") and health.get("opcua_feedback_active"):
            status += _say(lang, " O PLC comunica um erro ativo.", " The PLC reports an active error.")
        return status
    if name == "QUERY_MODE":
        if state.get("start") is None or any(state.get(key) is None for key in ("mode_fast", "mode_ideal", "mode_manual", "mode_change")):
            return _say(lang, "Não consigo confirmar o modo atual do PLC.",
                        "I cannot confirm the PLC's current mode.")
        if state.get("start") == 0:
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
        if not health.get("opcua_connected"):
            return _say(lang, "O OPC UA está desligado. Não consigo enviar comandos.",
                        "OPC UA is disconnected. I cannot send commands.")
        return _say(lang, "O servidor OPC UA está ligado e os estados são lidos. A ligação entre os PLCs não é verificável sem diagnóstico próprio."
                    if health.get("opcua_feedback_active") else "O servidor OPC UA está ligado, mas os estados não estão disponíveis.",
                    "The OPC UA server is connected and states are readable. The link between PLCs cannot be verified without its own diagnostics."
                    if health.get("opcua_feedback_active") else "The OPC UA server is connected, but states are unavailable.")
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
        if event.get("source") == "plc":
            return _say(lang, f"Último retorno do PLC: {event.get(f'detail_{lang}') or event.get('detail') or ''}",
                        f"Latest PLC return: {event.get(f'detail_{lang}') or event.get('detail') or ''}")
        if event.get("source") == "opcua":
            return _say(lang, f"Última etapa OPC UA: {event.get(f'detail_{lang}') or event.get('detail') or ''}",
                        f"Latest OPC UA stage: {event.get(f'detail_{lang}') or event.get('detail') or ''}")
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
        if not allowed:
            return _say(lang, "Podes consultar o estado, mas aguarda pela ligação ao PLC antes de comandar.",
                        "You can ask for status, but wait for the PLC connection before sending commands.")
        if allowed == {"STOP"}:
            return _say(lang, "Podes parar o sistema ou consultar o seu estado.",
                        "You can stop the system or ask for its status.")
        if "START" in allowed and not state.get("start"):
            return _say(lang, "Podes iniciar o sistema ou consultar o seu estado.",
                        "You can start the system or ask for its status.")
        if "MODE_FAST" in allowed and not any(state.get(key) for key in ("mode_fast", "mode_ideal", "mode_manual")):
            return _say(lang, "Podes escolher o modo rápido, ideal ou manual, ou parar o sistema.",
                        "You can choose fast, ideal or manual mode, or stop the system.")
        if "MOTOR_1_ON" in allowed:
            return _say(lang, "Podes comandar motores, cilindros A e B, pedir o avanço de C e D, controlar luzes e pedir recolha nos tapetes.",
                        "You can control motors, cylinders A and B, request C and D extension, control lights and request conveyor pickup.")
        return _say(lang, "Podes mudar de modo ou parar o sistema.", "You can change mode or stop the system.")
    return _say(lang, "Não percebi a consulta.", "I did not understand the question.")
