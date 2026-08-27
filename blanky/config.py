import os


def load_local_environment() -> bool:
    """Load the optional local OpenAI key without executing a shell file."""
    if os.environ.get("OPENAI_API_KEY"):
        return True

    env_path = os.environ.get(
        "BLANKY_ENV_FILE", os.path.join(os.path.expanduser("~"), ".blanky", "openai.env")
    )
    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[7:].strip()
                key, separator, value = line.partition("=")
                if key.strip() != "OPENAI_API_KEY" or not separator:
                    continue
                value = value.strip().strip('"').strip("'")
                if value:
                    os.environ["OPENAI_API_KEY"] = value
                    return True
    except OSError:
        pass
    return False

# ===== CONFIG =====
FS = 16000
SECONDS = 6
DEVICE_ID = None
AUDIO_PROFILE = "home"  # "home" | "lab"

# Perfil HOME: comportamento mais proximo do original (sem filtros extra)
if AUDIO_PROFILE == "home":
    AUDIO_VAD_CALIBRATION_SECONDS = 0.18
    AUDIO_VAD_WAIT_FOR_SPEECH_SECONDS = 0.70
    AUDIO_VAD_MIN_RECORD_SECONDS = 0.55
    AUDIO_VAD_MAX_RECORD_SECONDS = 3.20
    AUDIO_VAD_SILENCE_HOLD_SECONDS = 0.35
    AUDIO_VAD_TRIGGER_FACTOR = 1.65
    AUDIO_VAD_MIN_RMS = 0.002
    AUDIO_MAX_GAIN = 4.50
    AUDIO_FILTER_ENABLED = False
    AUDIO_HIGHPASS_HZ = 90.0
    AUDIO_NOISE_GATE_FACTOR = 1.9
    AUDIO_NOISE_GATE_BLEND = 0.18
    AUDIO_NOISE_PROFILE_SUBTRACT_ENABLED = False
    AUDIO_NOISE_SUBTRACT_FACTOR = 1.0
    AUDIO_NOISE_FLOOR_KEEP = 0.0
else:
    # Perfil LAB: robusto para ruido de fundo constante
    AUDIO_VAD_CALIBRATION_SECONDS = 0.28
    AUDIO_VAD_WAIT_FOR_SPEECH_SECONDS = 0.90
    AUDIO_VAD_MIN_RECORD_SECONDS = 0.65
    AUDIO_VAD_MAX_RECORD_SECONDS = 3.60
    AUDIO_VAD_SILENCE_HOLD_SECONDS = 0.42
    AUDIO_VAD_TRIGGER_FACTOR = 1.85
    AUDIO_VAD_MIN_RMS = 0.004
    AUDIO_MAX_GAIN = 3.60
    AUDIO_FILTER_ENABLED = False
    AUDIO_HIGHPASS_HZ = 110.0
    AUDIO_NOISE_GATE_FACTOR = 2.0
    AUDIO_NOISE_GATE_BLEND = 0.12
    AUDIO_NOISE_PROFILE_SUBTRACT_ENABLED = True
    AUDIO_NOISE_SUBTRACT_FACTOR = 0.30
    AUDIO_NOISE_FLOOR_KEEP = 0.12

MQTT_ENABLED = True
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = None
MQTT_PASSWORD = None
MQTT_CLIENT_ID = "blanky-controller"
MQTT_TOPIC_PREFIX = "blanky"
MQTT_PULSE_SECONDS = 3.0

OPCUA_ENABLED = True
OPCUA_URL = "opc.tcp://192.168.30.3:4840"
OPCUA_NAMESPACE_INDEX = 4
OPCUA_PULSE_SECONDS = 0.3

# A wake word esta desativada no prototipo; fica documentada para trabalho futuro.
WAKEWORD_ENABLED = False
WAKEWORD_THRESHOLD = 0.55
WAKEWORD_COOLDOWN_SECONDS = 2.5
WAKEWORD_SAMPLE_RATE = 16000
WAKEWORD_FRAME_MS = 80
WAKEWORD_MODEL_NAME = "hey jarvis"
WAKEWORD_MODEL_PATH = None

TTS_VOICES_PT = ["alloy", "nova", "shimmer", "sage", "coral", "fable"]
# Keep the same selectable voice names in Portuguese and English. The speech
# service still renders each preview in the active language.
TTS_VOICES_EN = list(TTS_VOICES_PT)
TTS_VOICE_DEFAULT_PT = "nova"
TTS_VOICE_DEFAULT_EN = "alloy"
STT_MODEL = "gpt-transcribe"
TTS_MODEL = "gpt-4o-mini-tts"

AUDIO_DIR = "audio"
INPUT_WAV = os.path.join(AUDIO_DIR, "input.wav")
TTS_WAV = os.path.join(AUDIO_DIR, "tts.wav")
BEEP_WAV = os.path.join(AUDIO_DIR, "beep.wav")

def ensure_dirs():
    os.makedirs(AUDIO_DIR, exist_ok=True)
