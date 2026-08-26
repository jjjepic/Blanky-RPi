import os
import sys

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from blanky.qml_controller import BlankyController


def run_app_qml():
    app = QGuiApplication(sys.argv)

    icon_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "assets", "blanky_logo_dark.png")
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    engine = QQmlApplicationEngine()
    controller = BlankyController()
    engine.rootContext().setContextProperty("blanky", controller)
    app.aboutToQuit.connect(controller.shutdown)

    qml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui", "Main.qml"))
    engine.load(qml_path)

    if not engine.rootObjects():
        raise RuntimeError(f"Falha ao carregar QML: {qml_path}")

    sys.exit(app.exec())
