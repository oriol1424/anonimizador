"""Punto de entrada de la aplicación de escritorio."""

import sys

from PySide6.QtWidgets import QApplication

from anonimizador.ui import style
from anonimizador.ui.main_window import MainWindow


def _window_check() -> str:
    """Abre la ventana sin mostrarla: comprueba que Qt, estilos e iconos cargan (paquete)."""
    import os
    import tempfile
    from pathlib import Path

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    style.apply(app)
    with tempfile.TemporaryDirectory() as tmp:
        window = MainWindow(keep_path=Path(tmp) / "k.json", log_path=Path(tmp) / "e.log")
        window.show()
        app.processEvents()
        title = window.windowTitle()
        window.close()
    return f"OK: finestra ({title})"


def main() -> int:
    if "--prova" in sys.argv:  # autoprueba sin ventana (ver core/selftest.py)
        from anonimizador.core import selftest

        args = sys.argv[sys.argv.index("--prova") + 1 :]
        return selftest.main(args[0] if args else None, window_check=_window_check)
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
