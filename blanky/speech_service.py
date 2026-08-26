from openai import OpenAI

from blanky.config import (
    STT_MODEL,
    TTS_MODEL,
    TTS_VOICE_DEFAULT_EN,
    TTS_VOICE_DEFAULT_PT,
    TTS_VOICES_EN,
    TTS_VOICES_PT,
)

client = OpenAI()
_ACTIVE_VOICE = TTS_VOICE_DEFAULT_PT


def set_openai_api_key(api_key: str):
    """Refresh the session client after the user changes the API key in settings."""
    global client
    client = OpenAI(api_key=api_key)


def _looks_like_prompt_echo(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    markers = [
        "comandos industriais curtos",
        "short industrial commands",
        "exemplos:",
        "examples:",
        "ativar motor 1",
        "activate motor 1",
    ]
    hits = sum(1 for m in markers if m in t)
    return hits >= 2


def get_tts_voice_options(lang: str) -> list[str]:
    if lang == "en":
        return list(TTS_VOICES_EN)
    return list(TTS_VOICES_PT)


def set_tts_voice(voice: str, lang: str) -> str:
    global _ACTIVE_VOICE
    options = get_tts_voice_options(lang)
    fallback = TTS_VOICE_DEFAULT_EN if lang == "en" else TTS_VOICE_DEFAULT_PT
    _ACTIVE_VOICE = voice if voice in options else fallback
    return _ACTIVE_VOICE


def get_tts_voice() -> str:
    return _ACTIVE_VOICE


def _transcribe_once(wav_path: str, lang: str, use_server_vad: bool):
    prompt_pt = "Transcreve apenas o comando ouvido. Nao inventes."
    prompt_en = "Transcribe only the spoken command. Do not invent words."
    prompt = prompt_pt if lang == "pt" else prompt_en

    kwargs = {
        "file": None,
        "model": STT_MODEL,
        "language": lang,
        "prompt": prompt,
        "temperature": 0,
    }
    if use_server_vad:
        kwargs["chunking_strategy"] = {
            "type": "server_vad",
            "threshold": 0.40,
            "silence_duration_ms": 260,
            "prefix_padding_ms": 180,
        }

    with open(wav_path, "rb") as f:
        kwargs["file"] = f
        return client.audio.transcriptions.create(**kwargs)


def stt_transcribe(wav_path: str, lang: str) -> str:
    try:
        primary = _transcribe_once(wav_path, lang, use_server_vad=False)
    except Exception:
        primary = None

    primary_text = (getattr(primary, "text", "") or "").strip()
    if primary_text and not _looks_like_prompt_echo(primary_text):
        return primary_text

    try:
        fallback = _transcribe_once(wav_path, lang, use_server_vad=True)
    except Exception:
        fallback = None

    if fallback is None:
        return ""

    fallback_text = (getattr(fallback, "text", "") or "").strip()
    if _looks_like_prompt_echo(fallback_text):
        return ""
    return fallback_text

def tts_speak_to_wav(
    text: str,
    out_wav_path: str,
    voice: str | None = None,
    speed: float | None = None,
    lang: str = "pt",
):
    playback_speed = max(0.25, min(4.0, float(speed if speed is not None else 1.0)))
    if playback_speed < 0.95:
        instructions = (
            "Fala mais devagar e com pausas claras."
            if lang == "pt"
            else "Speak slowly with clear pauses."
        )
    elif playback_speed > 1.05:
        instructions = (
            "Fala mais depressa, mantendo os comandos claros."
            if lang == "pt"
            else "Speak faster while keeping commands clear."
        )
    else:
        instructions = (
            "Fala num ritmo natural e claro para comandos industriais."
            if lang == "pt"
            else "Speak at a natural, clear pace for industrial commands."
        )
    speech = client.audio.speech.create(
        model=TTS_MODEL,
        voice=voice or _ACTIVE_VOICE,
        input=text,
        response_format="wav",
        instructions=instructions,
    )
    with open(out_wav_path, "wb") as f:
        f.write(speech.read())
