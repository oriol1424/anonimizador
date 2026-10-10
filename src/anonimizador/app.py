"""Punto de entrada de la aplicación de escritorio."""

import sys

from PySide6.QtWidgets import QApplication

from anonimizador.ui.main_window import MainWindow

STYLE = """
QWidget { font-size: 11pt; }
QGroupBox { font-weight: bold; margin-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QLabel#hint { color: palette(mid); font-weight: normal; }
QLabel#fileLabel { padding: 4px; }
QLabel#notices { background: #fff4ce; color: #4a3b00; padding: 8px; border-radius: 4px; }
QPushButton#primary {
    background: #2463eb; color: white; font-weight: bold; border-radius: 6px; padding: 6px 18px;
}
QPushButton#primary:disabled { background: #9db5ea; }
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Anonimitzador")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
