"""Punto de entrada de la aplicación de escritorio."""

import sys

from PySide6.QtWidgets import QApplication

from anonimizador.ui import style
from anonimizador.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Anonimitzador")
    style.apply(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
