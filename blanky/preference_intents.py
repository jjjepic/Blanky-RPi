"""Accessible read/write intents for existing UI and audio preferences only."""

from blanky.command_parser import VALID_SETTING_VALUES, VALID_SETTINGS
from blanky.config import TTS_VOICES_EN, TTS_VOICES_PT


def get_tts_voice_options(lang: str) -> list[str]:
    return list(TTS_VOICES_PT if lang == "pt" else TTS_VOICES_EN)


def _say(lang: str, pt: str, en: str) -> str:
    return pt if lang == "pt" else en


_LABELS = {
    "dark": ("escuro", "dark"), "light": ("claro", "light"),
    "high_contrast": ("alto contraste", "high contrast"),
    "colorblind": ("daltonismo", "color vision"),
    "monochrome": ("monocromático", "monochrome"),
    "custom": ("personalizado", "custom"),
    "simple": ("simples", "simple"), "balanced": ("equilibrado", "balanced"),
    "noisy": ("ruidoso", "noisy"), "auto": ("automática", "automatic"),
    "online": ("Online", "Online"), "offline": ("Offline", "Offline"),
    "pt": ("português", "Portuguese"), "en": ("inglês", "English"),
    "slow": ("lenta", "slow"), "normal": ("normal", "normal"),
    "fast": ("rápida", "fast"), "on": ("ligadas", "on"), "off": ("desligadas", "off"),
    "universal": ("universal", "universal"), "protan": ("protan", "protan"),
    "deutan": ("deutan", "deutan"), "tritan": ("tritan", "tritan"),
    "compact_1280": ("compacta", "compact"), "hd_1366": ("HD", "HD"),
    "large_1600": ("grande", "large"), "full_hd": ("Full HD", "Full HD"),
}


def _label(value: str, lang: str) -> str:
    return _LABELS.get(value, (value, value))[0 if lang == "pt" else 1]


def _snapshot(controller, target: str) -> str:
    return {
        "voice": lambda: controller.ttsVoice,
        "speech_speed": lambda: "slow" if controller.ttsSpeed < 0.9 else "fast" if controller.ttsSpeed > 1.1 else "normal",
        "volume": lambda: str(round(controller.soundVolume * 100)),
        "language": lambda: controller.language,
        "appearance": lambda: controller.appearanceMode,
        "color_profile": lambda: controller.colorVisionProfile,
        "audio_profile": lambda: controller.audioSelectedProfile,
        "text_scale": lambda: str(round(controller.appearanceTextScale * 100)),
        "animations": lambda: "on" if controller.hoverAnimationsEnabled else "off",
        "display_scale": lambda: controller.displayScaleProfile,
        "textbot_mode": lambda: controller.textBotMode,
    }[target]()


def _answer(target: str, value: str, lang: str, changed: bool) -> str:
    label = _label(value, lang)
    templates = {
        "voice": (f"Voz {'alterada para ' if changed else 'atual: '}{label.capitalize()}.",
                  f"Voice {'changed to ' if changed else 'currently '}{label.capitalize()}."),
        "speech_speed": (f"Velocidade da fala: {label}.", f"Speech speed: {label}."),
        "volume": (f"Volume a {value} por cento.", f"Volume at {value} percent."),
        "language": (f"Idioma: {label}.", f"Language: {label}."),
        "appearance": (f"Aspeto: {label}.", f"Appearance: {label}."),
        "color_profile": (f"Perfil cromático: {label}.", f"Color profile: {label}."),
        "audio_profile": (f"Perfil de áudio: {label}.", f"Audio profile: {label}."),
        "text_scale": (f"Tamanho do texto: {value} por cento.", f"Text size: {value} percent."),
        "animations": (f"Animações {label}.", f"Animations {label}."),
        "display_scale": (f"Escala do ecrã: {label}.", f"Display scale: {label}."),
        "textbot_mode": (f"Text-Bot em modo {label}.", f"Text-Bot in {label} mode."),
        "voices": ("Vozes disponíveis: " + ", ".join(get_tts_voice_options("pt")) + ".",
                   "Available voices: " + ", ".join(get_tts_voice_options("en")) + "."),
    }
    return templates[target][0 if lang == "pt" else 1]


def _change(controller, target: str, value: str) -> bool:
    """Call only existing, whitelisted controller setters. Return whether clamped."""
    current = _snapshot(controller, target)
    clipped = False
    if target == "voice":
        options = get_tts_voice_options(controller.language)
        selected = options[(options.index(current) + 1) % len(options)] if value == "next" else value
        if selected not in options:
            raise ValueError("voice")
        controller.setTtsVoice(selected)
    elif target == "speech_speed":
        options = (0.8, 1.0, 1.2)
        selected = {"slow": 0.8, "normal": 1.0, "fast": 1.2}.get(value)
        if value in {"increase", "decrease"}:
            offset = 1 if value == "increase" else -1
            selected = options[max(0, min(2, options.index(controller.ttsSpeed) + offset))]
        if selected is None:
            raise ValueError("speech_speed")
        controller.setTtsSpeed(selected)
    elif target == "volume":
        if value in {"increase", "decrease"}:
            selected = round(controller.soundVolume * 100) + (10 if value == "increase" else -10)
        elif value.isdigit():
            selected = int(value)
        else:
            raise ValueError("volume")
        clipped = not 0 <= selected <= 100
        controller.setSoundVolume(max(0, min(100, selected)) / 100)
    elif target == "language":
        if value not in {"pt", "en"}:
            raise ValueError("language")
        controller.setLanguage(value)
    elif target == "appearance":
        if value in {"protan", "deutan", "tritan", "universal"}:
            controller.setColorVisionProfile(value)
        elif value in {"dark", "light", "high_contrast", "colorblind", "monochrome", "custom"}:
            controller.setAppearanceMode(value)
        else:
            raise ValueError("appearance")
    elif target == "color_profile":
        if value not in {"universal", "protan", "deutan", "tritan"}:
            raise ValueError("color_profile")
        controller.setColorVisionProfile(value)
    elif target == "audio_profile":
        if value not in {"simple", "balanced", "noisy"}:
            raise ValueError("audio_profile")
        controller.setAudioInputPreset(value)
    elif target == "text_scale":
        selected = (round(controller.appearanceTextScale * 100) + (10 if value == "increase" else -10)
                    if value in {"increase", "decrease"} else int(value) if value.isdigit() else None)
        if selected is None:
            raise ValueError("text_scale")
        clipped = not 100 <= selected <= 125
        controller.setAppearanceTextScale(max(100, min(125, selected)) / 100)
    elif target == "animations":
        if value not in {"on", "off"}:
            raise ValueError("animations")
        controller.setHoverAnimationsEnabled(value == "on")
    elif target == "display_scale":
        if value not in {"auto", "compact_1280", "hd_1366", "large_1600", "full_hd"}:
            raise ValueError("display_scale")
        controller.setDisplayScaleProfile(value)
    elif target == "textbot_mode":
        if value not in {"online", "offline"}:
            raise ValueError("textbot_mode")
        controller.setTextBotMode(value)
    else:
        raise ValueError(target)
    return clipped


def handle_preference(controller, item: dict, lang: str) -> dict[str, dict[str, str]]:
    """Return bilingual speech/detail; no command or PLC method is called."""
    target = item.get("target", "")
    kind = item.get("type")
    value = item.get("value", "")
    if item.get("name") in {"BLOCKED_SETTING", "QUERY_CLARIFY"}:
        answers = {}
        for language in ("pt", "en"):
            if item["name"] == "BLOCKED_SETTING":
                speech = _say(language, "As definições de comunicação só mudam no menu.",
                              "Communication settings can only be changed in the menu.")
                detail = speech + _say(language, " Nenhum parâmetro foi alterado.", " No parameter was changed.")
            else:
                label = _say(language, "volume", "volume") if target == "volume" else target.replace("_", " ")
                speech = _say(language, f"Queres saber o {label} ou alterá-lo?",
                              f"Do you want to check or change the {label}?")
                detail = speech
            answers[language] = {"speech": speech, "detail": detail}
        return answers
    if target not in VALID_SETTINGS or (kind == "setting" and (target == "voices" or value not in VALID_SETTING_VALUES)):
        raise ValueError("unsupported preference")
    if kind == "setting":
        clipped = _change(controller, target, value)
    elif kind == "query":
        clipped = False
    else:
        raise ValueError("unsupported intent")
    actual = "" if target == "voices" else _snapshot(controller, target)
    answers = {}
    for language in ("pt", "en"):
        speech = _answer(target, actual, language, kind == "setting")
        if kind == "setting" and target == "appearance" and value in {"protan", "deutan", "tritan", "universal"}:
            speech = _say(language, f"Aspeto: daltonismo, perfil {value}.",
                          f"Appearance: color vision, {value} profile.")
        if clipped:
            speech += _say(language, " Ajustado ao limite permitido.", " Adjusted to the allowed limit.")
        detail = speech + _say(language, " Definição local do Blanky; sem comando enviado ao PLC.",
                               " Local Blanky preference; no command sent to the PLC.")
        answers[language] = {"speech": speech, "detail": detail}
    return answers
