from blanky.config import ensure_dirs
from blanky.audio_service import init_audio
from blanky.qml_app import run_app_qml


def main():
    ensure_dirs()
    init_audio()
    run_app_qml()


if __name__ == "__main__":
    main()
