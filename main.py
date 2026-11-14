from blanky.config import ensure_dirs, load_local_environment

# Optional local credentials must be available before importing services that use OpenAI.
load_local_environment()

from blanky.audio_service import init_audio
from blanky.qml_app import run_app_qml
import logging


def main():
    ensure_dirs()
    try:
        init_audio()
    except Exception as exc:
        logging.getLogger(__name__).warning("Audio input unavailable at startup; will retry on capture: %s", exc)
    run_app_qml()


if __name__ == "__main__":
    main()
