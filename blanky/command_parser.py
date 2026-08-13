import json
import os
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Tuple

from openai import OpenAI

BASE_DIR = os.path.dirname(__file__)
JSON_PATH = os.path.join(BASE_DIR, "commands.json")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    DATA = json.load(f)

CATALOG_DESCRIPTIONS = {
    "pt": {
        "START": "Inicia o sistema.",
        "STOP": "Para e repõe todos os componentes.",
        "MODE_FAST": "Seleciona o modo rápido.",
        "MODE_IDEAL": "Seleciona o modo ideal.",
        "MODE_MANUAL": "Seleciona o modo manual.",
        "MODE_CHANGE": "Permite escolher outro modo.",
        "MOTOR_ON/OFF": "Ativa ou desativa um motor.",
        "CYL_EXTEND/RETRACT": "Avança ou recua um cilindro.",
        "GREEN_ON/OFF": "Liga ou desliga a luz verde.",
        "RED_ON/OFF": "Liga ou desliga a luz vermelha.",
        "ROBOT_TO_METAL/NONMETAL": "Envia o robô para metal ou não metal.",
    },
    "en": {
        "START": "Starts the system.",
        "STOP": "Stops and resets all components.",
        "MODE_FAST": "Selects fast mode.",
        "MODE_IDEAL": "Selects ideal mode.",
        "MODE_MANUAL": "Selects manual mode.",
        "MODE_CHANGE": "Allows selecting another mode.",
        "MOTOR_ON/OFF": "Activates or deactivates a motor.",
        "CYL_EXTEND/RETRACT": "Extends or retracts a cylinder.",
        "GREEN_ON/OFF": "Turns the green light on or off.",
        "RED_ON/OFF": "Turns the red light on or off.",
        "ROBOT_TO_METAL/NONMETAL": "Sends the robot to metal or non-metal.",
    },
}

VALID_COMMANDS = frozenset({
    "START", "STOP", "MODE_FAST", "MODE_IDEAL", "MODE_MANUAL", "MODE_UNSPEC",
    "MOTOR_1_ON", "MOTOR_1_OFF", "MOTOR_2_ON", "MOTOR_2_OFF", "MOTOR_3_ON", "MOTOR_3_OFF",
    "CYL_A_EXTEND", "CYL_A_RETRACT", "CYL_B_EXTEND", "CYL_B_RETRACT",
    "CYL_C_EXTEND", "CYL_C_RETRACT", "CYL_D_EXTEND", "CYL_D_RETRACT",
    "GREEN_ON", "GREEN_OFF", "RED_ON", "RED_OFF", "ROBOT_TO_METAL", "ROBOT_TO_NONMETAL",
})


def interpret_online_commands(raw_text: str, lang: str) -> list[str]:
    """Use the AI only to map natural text to a validated canonical command list."""
    language = "Portuguese" if lang == "pt" else "English"
    allowed = ", ".join(sorted(VALID_COMMANDS))
    prompt = (
        "You are a strict industrial command interpreter. Return JSON only, in the form "
        '{"commands": ["COMMAND"]}. Extract one or more actions from the user text, preserve their order, '
        "and return an empty array if no safe action is explicit. Never invent commands, explanations, "
        f"or extra fields. The user language is {language}. Allowed commands are: {allowed}. "
        f"User text: {raw_text}"
    )
    client = OpenAI()
    response = client.chat.completions.create(
        model=os.getenv("BLANKY_TEXTBOT_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    payload = json.loads(content)
    commands = payload.get("commands", [])
    if not isinstance(commands, list):
        return []
    return [str(command).upper() for command in commands if str(command).upper() in VALID_COMMANDS]


def normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")  # remove acentos
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)  # mantém hífen para "nao-metal"
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains_any_substring(text: str, items: list[str]) -> bool:
    # Match robusto por fronteiras para reduzir falsos positivos por substring.
    padded = f" {text} "
    for it in items:
        token = (it or "").strip().lower()
        if not token:
            continue
        if " " in token or "-" in token:
            if f" {token} " in padded:
                return True
            continue
        if re.search(rf"\b{re.escape(token)}\b", text):
            return True
    return False


def motor_number(text: str):
    # aceita 1/2/3 e um/dois/tres e one/two/three
    m = re.search(r"\bmotor\b.*\b(1|2|3|um|dois|tres|one|two|three)\b", text)
    if not m:
        return None
    val = m.group(1)
    mapping = {"um": 1, "one": 1, "dois": 2, "two": 2, "tres": 3, "three": 3}
    if val.isdigit():
        return int(val)
    return mapping.get(val)


def cylinder_letter(text: str):
    m = re.search(r"\b(a|b|c|d)\b", text)
    return m.group(1).upper() if m else None


def resolve_mode_command(text: str, data: dict) -> str:
    """Recognise an explicit mode request, including small STT spelling changes."""
    tokens = text.split()
    direct_mode_request = len(tokens) <= 3 or "modo" in text or "mode" in text
    if not direct_mode_request:
        return ""

    mode_sets = (
        ("MODE_FAST", data.get("mode_fast_ph", []) + data.get("mode_fast_words", [])),
        ("MODE_IDEAL", data.get("mode_ideal_ph", []) + data.get("mode_ideal_words", [])),
        ("MODE_MANUAL", data.get("mode_manual_ph", []) + data.get("mode_manual_words", [])),
    )
    for command, variants in mode_sets:
        if contains_any_substring(text, variants):
            return command

    # Restrict fuzzy matching to very short requests so ordinary speech is not a command.
    if not 1 <= len(tokens) <= 3:
        return ""
    for token in tokens:
        if len(token) < 5:
            continue
        for command, variants in mode_sets:
            for variant in variants:
                candidate = normalize(variant)
                if " " in candidate or len(candidate) < 5:
                    continue
                if SequenceMatcher(None, token, candidate).ratio() >= 0.84:
                    return command
    return ""


def parse_command(raw_text: str, lang: str) -> Tuple[str, str]:
    text = normalize(raw_text)
    if not text:
        return "NO_AUDIO", "(sem áudio detetado)" if lang == "pt" else "(no audio detected)"

    d = DATA.get(lang, DATA["pt"])
    # ============ START/STOP ============
    if contains_any_substring(text, d["start"]):
        return "START", "Iniciado." if lang == "pt" else "Started."
    if contains_any_substring(text, d["stop"]):
        return "STOP", "Parado." if lang == "pt" else "Stopped."

    # ============ MODOS ============
    # PT: pode vir "mudar modo", ou apenas conter "modo ..."
    # EN: idem com "mode"
    change_mode = (
        contains_any_substring(text, d.get("change_mode_ph", []))
        or contains_any_substring(text, d.get("change_mode_words", []))
        or ("modo" in text if lang == "pt" else "mode" in text)
    )
    mode_command = resolve_mode_command(text, d)
    if mode_command:
        if mode_command == "MODE_FAST":
            return mode_command, "Modo rapido ativado." if lang == "pt" else "Fast mode enabled."
        if mode_command == "MODE_IDEAL":
            return mode_command, "Modo ideal ativado." if lang == "pt" else "Ideal mode enabled."
        return mode_command, "Modo manual ativado." if lang == "pt" else "Manual mode enabled."

    if change_mode:
        fast = d.get("mode_fast_ph", []) + d.get("mode_fast_words", [])
        ideal = d.get("mode_ideal_ph", []) + d.get("mode_ideal_words", [])
        manual = d.get("mode_manual_ph", []) + d.get("mode_manual_words", [])

        if contains_any_substring(text, fast):
            return "MODE_FAST", "Modo rápido ativado." if lang == "pt" else "Fast mode enabled."
        if contains_any_substring(text, ideal):
            return "MODE_IDEAL", "Modo ideal ativado." if lang == "pt" else "Ideal mode enabled."
        if contains_any_substring(text, manual):
            return "MODE_MANUAL", "Modo manual ativado." if lang == "pt" else "Manual mode enabled."

        # pediu modo mas não disse qual
        return "MODE_UNSPEC", "Qual modo? Rápido, ideal ou manual." if lang == "pt" else "Which mode? Fast, ideal or manual."

    # ============ LUZES (OFF antes de ON) ============
    # PT
    if lang == "pt":
        is_green = contains_any_substring(text, d["light_green"])
        is_red = contains_any_substring(text, d["light_red"])
        if is_green:
            if contains_any_substring(text, d["light_off"]):
                return "GREEN_OFF", "Luz verde apagada."
            if contains_any_substring(text, d["light_on"]):
                return "GREEN_ON", "Luz verde acesa."
        if is_red:
            if contains_any_substring(text, d["light_off"]):
                return "RED_OFF", "Luz vermelha apagada."
            if contains_any_substring(text, d["light_on"]):
                return "RED_ON", "Luz vermelha acesa."
    else:
        # EN (palavras + frases)
        is_green = contains_any_substring(text, d["light_green"])
        is_red = contains_any_substring(text, d["light_red"])
        light_on = d.get("light_on_ph", []) + d.get("light_on_words", [])
        light_off = d.get("light_off_ph", []) + d.get("light_off_words", [])

        if is_green:
            if contains_any_substring(text, light_off):
                return "GREEN_OFF", "Green light off."
            if contains_any_substring(text, light_on):
                return "GREEN_ON", "Green light on."
        if is_red:
            if contains_any_substring(text, light_off):
                return "RED_OFF", "Red light off."
            if contains_any_substring(text, light_on):
                return "RED_ON", "Red light on."

    # ============ ROBOT ============
    if contains_any_substring(text, d["robot_word"]) and contains_any_substring(text, d["robot_go"]):
        if contains_any_substring(text, d["nonmetal"]):
            return "ROBOT_TO_NONMETAL", "Robô a ir para não metal." if lang == "pt" else "Robot moving to non-metal."
        if contains_any_substring(text, d["metal"]):
            return "ROBOT_TO_METAL", "Robô a ir para metal." if lang == "pt" else "Robot moving to metal."

    # ============ MOTOR 1/2/3 ============
    if contains_any_substring(text, d["motor_word"]):
        m = motor_number(text)
        if m in (1, 2, 3):
            # prioridade OFF antes de ON
            if contains_any_substring(text, d.get("deactivate_ph", [])) or contains_any_substring(text, d["deactivate"]):
                return f"MOTOR_{m}_OFF", (f"Motor {m} desativado." if lang == "pt" else f"Motor {m} deactivated.")
            if contains_any_substring(text, d.get("activate_ph", [])) or contains_any_substring(text, d["activate"]):
                return f"MOTOR_{m}_ON", (f"Motor {m} ativado." if lang == "pt" else f"Motor {m} activated.")

    # ============ CILINDRO/VALVULA A-D ============
    if contains_any_substring(text, d["cylinder_word"]):
        letter = cylinder_letter(text)
        if letter in ("A", "B", "C", "D"):
            # retract/off prioridade
            if (
                contains_any_substring(text, d.get("deactivate_ph", []))
                or contains_any_substring(text, d["deactivate"])
                or contains_any_substring(text, d["cylinder_retract"])
            ):
                return f"CYL_{letter}_RETRACT", (
                    f"Cilindro {letter} a recuar." if lang == "pt" else f"Cylinder {letter} retracting."
                )
            if contains_any_substring(text, d.get("activate_ph", [])) or contains_any_substring(text, d["activate"]):
                return f"CYL_{letter}_EXTEND", (
                    f"Cilindro {letter} a avançar." if lang == "pt" else f"Cylinder {letter} extending."
                )

    return "UNKNOWN", "Comando não reconhecido." if lang == "pt" else "Command not recognized."

def command_catalog_text(lang: str) -> str:
    d = DATA.get(lang, DATA["pt"])
    descriptions = CATALOG_DESCRIPTIONS.get(lang, CATALOG_DESCRIPTIONS["pt"])
    lines: list[str] = []
    lines.append("=== COMANDOS DISPONIVEIS ===" if lang == "pt" else "=== AVAILABLE COMMANDS ===")
    lines.append("")

    sections = [
        ("START", d.get("start", [])),
        ("STOP", d.get("stop", [])),
        ("MODE_FAST", d.get("mode_fast_ph", []) + d.get("mode_fast_words", [])),
        ("MODE_IDEAL", d.get("mode_ideal_ph", []) + d.get("mode_ideal_words", [])),
        ("MODE_MANUAL", d.get("mode_manual_ph", []) + d.get("mode_manual_words", [])),
        ("MODE_CHANGE", d.get("change_mode_ph", []) + d.get("change_mode_words", [])),
        ("MOTOR_ON/OFF", d.get("motor_word", []) + d.get("activate", []) + d.get("deactivate", [])),
        ("CYL_EXTEND/RETRACT", d.get("cylinder_word", []) + d.get("cylinder_retract", []) + d.get("activate", [])),
        ("GREEN_ON/OFF", d.get("light_green", []) + d.get("light_on", []) + d.get("light_off", [])),
        ("RED_ON/OFF", d.get("light_red", []) + d.get("light_on", []) + d.get("light_off", [])),
        ("ROBOT_TO_METAL/NONMETAL", d.get("robot_word", []) + d.get("robot_go", []) + d.get("metal", []) + d.get("nonmetal", [])),
    ]

    for title, words in sections:
        uniq = []
        seen = set()
        for w in words:
            if w not in seen:
                uniq.append(w)
                seen.add(w)
        if not uniq:
            continue
        lines.append(f"{title}: {descriptions.get(title, '')}".rstrip())
        lines.append(", ".join(uniq))
        lines.append("")

    return "\n".join(lines).strip()
