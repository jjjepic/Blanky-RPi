"""Conservative local recognition of read-only questions and safe preferences."""

import re
import unicodedata
from difflib import get_close_matches


def normal(text: str) -> str:
    text = unicodedata.normalize("NFD", (text or "").lower())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text)).strip()


def _words(text: str) -> list[str]:
    aliases = {
        "bolume": "volume", "volum": "volume", "volome": "volume",
        "cilindru": "cilindro", "cilintro": "cilindro", "motore": "motor",
        "doiz": "dois", "be": "b", "bee": "b", "bae": "b",
    }
    return [aliases.get(word, word) for word in normal(text).split()]


def _match(text: str, words: tuple[str, ...]) -> bool:
    tokens = text.split()
    for token in tokens:
        if token in words:
            return True
        if len(token) >= 5 and get_close_matches(token, words, n=1, cutoff=0.84):
            return True
    return False


_SETTING_WORDS = {
    "voice": ("voz", "voice"),
    "volume": ("volume", "som", "alto", "baixo", "louder", "quieter"),
    "language": ("idioma", "lingua", "language", "portugues", "ingles", "english"),
    "appearance": ("tema", "aparencia", "aspecto", "aspeto", "theme", "appearance"),
    "color_profile": ("cromatico", "daltonismo", "protan", "deutan", "tritan", "universal", "colorblind"),
    "audio_profile": ("audio", "microfone", "microphone"),
    "text_scale": ("letra", "texto", "fonte", "reading", "text", "font"),
    "animations": ("animacoes", "animacao", "animations", "animation"),
    "display_scale": ("escala", "ecra", "monitor", "resolucao", "display", "screen", "resolution"),
    "textbot_mode": ("textbot", "text", "bot"),
    "voices": ("vozes", "voices"),
}
_BLOCKED = ("mqtt", "opc", "openai", "api", "chave", "password", "senha", "broker", "servidor", "server")


def _target(text: str) -> str:
    if "text bot" in text or "textbot" in text:
        return "textbot_mode"
    if (re.search(r"\b(tema|aparencia|aspecto|aspeto|theme|appearance|monocromatico|monochrome|daltonismo|colorblind)\b", text)
            or "alto contraste" in text or "high contrast" in text
            or re.search(r"\b(muda|mudar|switch|change)\s+(?:para|to)\s+(?:o\s+)?(?:claro|escuro|light mode|dark mode)\b", text)):
        return "appearance"
    speed = r"\b(velocidade|speed|devagar|depressa|rapido|rapida|lentamente|lenta|lento|fast|faster|slow|slower|slowly|quickly)\b"
    speech = r"\b(fala|falar|voz|le|ler|leitura|speech|speak|voice|read|talk)\b"
    if re.search(speed, text) and re.search(speech, text):
        return "speech_speed"
    if "perfil" in text and "audio" in text:
        return "audio_profile"
    if "profile" in text and "audio" in text:
        return "audio_profile"
    if "perfil" in text and ("cor" in text or "cromatic" in text):
        return "color_profile"
    if "color" in text and "profile" in text:
        return "color_profile"
    if ("tamanho" in text and "texto" in text) or "text size" in text:
        return "text_scale"
    for target, words in _SETTING_WORDS.items():
        if target == "voices":
            continue
        if _match(text, words):
            return target
    if _match(text, _SETTING_WORDS["voices"]):
        return "voices"
    return ""


def parse_preference(text: str, lang: str) -> dict | None:
    """Return a preference intent; blocked communications settings are never routed here."""
    phrase = " ".join(_words(text))
    if not phrase:
        return None
    if _match(phrase, _BLOCKED):
        if re.search(r"\b(chave|key|password|senha|broker|servidor|server|configurar|configura|definicoes|settings|muda|altera|change|set)\b", phrase):
            return {"type": "setting", "name": "BLOCKED_SETTING", "target": "", "value": "", "confidence": 1.0}
        return None
    target = _target(phrase)
    if not target:
        return None
    ask = bool(re.search(r"\b(qual|quais|que|quanto|como|what|which|how|tell|diz|estou|estas|current|atual)\b", phrase)) or ("?" in text and not re.search(r"\b(podes|can you|could you)\b", phrase))
    change = bool(re.search(r"\b(muda|mudar|altera|alterar|poe|coloca|mete|aumenta|reduz|diminui|liga|desliga|ativa|desativa|fala|change|set|switch|increase|decrease|turn|make|speak)\b", phrase))
    # Questions about the current value take precedence over verbs such as "diz".
    if ask and not re.search(r"\b(podes|can you|could you)\b", phrase):
        return {"type": "query", "name": "QUERY_SETTING", "target": target, "value": "", "confidence": 0.9}
    if target == "voices" and (ask or "disponiveis" in phrase or "available" in phrase):
        return {"type": "query", "name": "QUERY_SETTING", "target": "voices", "value": "", "confidence": 0.9}
    value = ""
    for token in ("alloy", "nova", "shimmer", "sage", "coral", "fable", "deutan", "protan", "tritan",
                  "monochrome", "monocromatico", "colorblind", "daltonismo", "high_contrast", "contraste",
                  "balanced", "equilibrado", "noisy", "ruidoso", "simple", "simples", "manual",
                  "universal", "personalizado",
                  "offline", "online", "automatico", "auto", "compact_1280", "hd_1366", "large_1600", "full_hd"):
        if token.replace("_", " ") in phrase:
            value = {"monocromatico": "monochrome", "daltonismo": "colorblind", "contraste": "high_contrast",
                     "equilibrado": "balanced", "ruidoso": "noisy", "simples": "simple",
                     "personalizado": "custom", "automatico": "auto"}.get(token, token)
            break
    if target == "language":
        value = "en" if re.search(r"\b(ingles|english)\b", phrase) else "pt" if re.search(r"\b(portugues|portuguese)\b", phrase) else value
    elif target == "appearance":
        value = "light" if re.search(r"\b(claro|clara|light)\b", phrase) else "dark" if re.search(r"\b(escuro|escura|dark)\b", phrase) else value
    elif target == "speech_speed":
        value = "slow" if re.search(r"\b(devagar|lentamente|lenta|lento|slow|slower|slowly)\b", phrase) else "fast" if re.search(r"\b(depressa|rapido|rapida|fast|faster|quickly)\b", phrase) else value
        if not value and re.search(r"\b(normal|normalmente)\b", phrase):
            value = "normal"
    elif target == "animations":
        value = "off" if re.search(r"\b(desliga|desativa|off|disable)\b", phrase) else "on" if re.search(r"\b(liga|ativa|on|enable)\b", phrase) else value
    elif target == "display_scale":
        value = ("full_hd" if "full hd" in phrase or "1080" in phrase else
                 "compact_1280" if re.search(r"\b(compacto|compacta|1280)\b", phrase) else
                 "hd_1366" if re.search(r"\b(1366|hd)\b", phrase) else
                 "large_1600" if re.search(r"\b(1600|grande|large)\b", phrase) else value)
    if not value:
        number = re.search(r"\b(\d{1,3})\b", phrase)
        if number:
            value = number.group(1)
        elif re.search(r"\b(mais|maior|aumenta|alto|louder|faster|increase|bigger|larger)\b", phrase):
            value = "increase"
        elif re.search(r"\b(menos|menor|reduz|diminui|baixo|quieter|slower|decrease|smaller)\b", phrase):
            value = "decrease"
        elif re.search(r"\b(outra|outro|another|next)\b", phrase):
            value = "next"
    if not change and not value:
        if len(phrase.split()) <= 2:
            return {"type": "query", "name": "QUERY_CLARIFY", "target": target, "value": "", "confidence": 0.6}
        return None
    if value:
        return {"type": "setting", "name": "SET_SETTING", "target": target, "value": value, "confidence": 0.9}
    return None


def parse_group_question(text: str, lang: str) -> dict | None:
    phrase = " ".join(_words(text))
    if not phrase:
        return None
    question = bool(re.search(r"\b(quais|quantos|que|ha|estao|esta|como|diz|what|which|how|are|is|any|tell)\b", phrase)) or "?" in text
    if not question:
        return None
    group = ""
    if re.search(r"\b(motores|motors)\b", phrase):
        group = "motors"
    elif re.search(r"\b(cilindros|cylinders)\b", phrase):
        group = "cylinders"
    elif re.search(r"\b(luzes|lights)\b", phrase):
        group = "lights"
    elif re.search(r"\b(robo|robot)\b", phrase):
        group = "robot"
    elif re.search(r"\b(tudo|componentes|everything|components)\b", phrase) and re.search(r"\b(ativo|ativos|ligado|ligados|active|on)\b", phrase):
        group = "all"
    if not group:
        return None
    if group == "lights" and not re.search(r"\b(acesas|apagadas|ligadas|desligadas|on|off|active)\b", phrase):
        return None
    # A named component is handled by QUERY_COMPONENT instead.
    if group == "motors" and re.search(r"\b(motor|motores|motors?)\s+(1|2|3|um|dois|tres|one|two|three)\b", phrase):
        return None
    if group == "cylinders" and re.search(r"\b(cilindro|cilindros|cylinders?)\s+[abcd]\b", phrase):
        return None
    value = ""
    if re.search(r"\b(desligados|desligadas|apagadas|off)\b", phrase):
        value = "off"
    elif re.search(r"\b(recuados|recolhidos|retracted)\b", phrase):
        value = "retracted"
    elif re.search(r"\b(avancados|extended)\b", phrase):
        value = "extended"
    elif re.search(r"\b(ligados|ligadas|acesas|ativos|ativas|on|active)\b", phrase):
        value = "on"
    name = "QUERY_ACTIVE" if group == "all" else "QUERY_COMPONENT_GROUP"
    return {"type": "query", "name": name, "target": "" if name == "QUERY_ACTIVE" else group,
            "value": "" if name == "QUERY_ACTIVE" else value, "confidence": 0.9}
