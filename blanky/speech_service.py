import os

from openai import OpenAI
from blanky.openai_activity import measure_request

from blanky.config import (
    STT_MODEL,
    TTS_MODEL,
    TTS_VOICE_DEFAULT_EN,
    TTS_VOICE_DEFAULT_PT,
    TTS_VOICES_EN,
    TTS_VOICES_PT,
)

client = None
_client_api_key = ""
_ACTIVE_VOICE = TTS_VOICE_DEFAULT_PT


def set_openai_api_key(api_key: str):
    """Refresh the session client after the user changes the API key in settings."""
    global client, _client_api_key
    _client_api_key = (api_key or "").strip()
    client = OpenAI(api_key=_client_api_key) if _client_api_key else None


def is_openai_configured() -> bool:
    return bool(_client_api_key or os.environ.get("OPENAI_API_KEY"))


def _get_client():
    """Create an OpenAI client only when an online speech feature is used."""
    global client, _client_api_key
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    if client is None or api_key != _client_api_key:
        client = OpenAI(api_key=api_key)
        _client_api_key = api_key
    return client


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
        with measure_request("STT"):
            return _get_client().audio.transcriptions.create(**kwargs)


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
    instructions = (
        "Fala em português europeu, de forma natural e próxima. Usa entoação suave, "
        "pausas breves na pontuação e dicção clara para nomes e estados da máquina. "
        "Evita um tom robótico ou dramático; não acrescentes palavras."
        if lang == "pt" else
        "Speak naturally and warmly, with gentle intonation and brief pauses at punctuation. "
        "Keep machine names and states clear, without sounding robotic or adding words."
    )
    with measure_request("TTS"):
        speech = _get_client().audio.speech.create(
            model=TTS_MODEL,
            voice=voice or _ACTIVE_VOICE,
            input=text,
            response_format="wav",
            instructions=instructions,
            speed=playback_speed,
        )
        audio_bytes = speech.read()
    with open(out_wav_path, "wb") as f:
        f.write(audio_bytes)
