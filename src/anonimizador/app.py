"""Punto de entrada de la aplicación de escritorio."""

import sys

from PySide6.QtWidgets import QApplication

from anonimizador.ui import style
from anonimizador.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Anonimitzador")
    app.setWindowIcon(style.app_icon())
    style.apply(app)
    window = MainWindow()

    def unexpected(kind, error, tb) -> None:
        """Errores no previstos fuera de las tareas: se registran (sin texto) y se avisa."""
        window._failed(error.with_traceback(tb))

    sys.excepthook = unexpected
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
