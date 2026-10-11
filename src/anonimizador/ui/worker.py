"""Ejecuta tareas largas fuera del hilo de la interfaz para que la ventana no se congele."""

from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal

from anonimizador.core.keep_awake import keep_awake

# Las señales deben vivir hasta que el resultado llegue al hilo de la interfaz; si Python las
# recolecta antes, el aviso se pierde y la ventana se queda "Treballant…" para siempre.
_alive: set["_Signals"] = set()


class _Signals(QObject):
    finished = Signal(object)
    failed = Signal(object)
    progress = Signal(int, int)


class _Task(QRunnable):
    def __init__(self, fn: Callable[[Callable[[int, int], None]], object], signals: _Signals):
        super().__init__()
        self.fn = fn
        self.signals = signals

    def run(self) -> None:
        try:
            with keep_awake():  # que el ordenador no se duerma a media tarea
                result = self.fn(self.signals.progress.emit)
        except Exception as exc:  # se muestra al usuario en la ventana
            self.signals.failed.emit(exc)
        else:
            self.signals.finished.emit(result)


def run_in_background(
    fn: Callable[[Callable[[int, int], None]], object],
    on_finished: Callable[[object], None],
    on_failed: Callable[[Exception], None],
    on_progress: Callable[[int, int], None] | None = None,
) -> None:
    """Ejecuta `fn(progress)` en otro hilo; las respuestas llegan al hilo de la interfaz.

    `fn` recibe una función `progress(hecho, total)` para informar de su avance.
    """
    signals = _Signals()  # creado aquí -> pertenece al hilo de la interfaz
    _alive.add(signals)

    def done(callback: Callable[[object], None]) -> Callable[[object], None]:
        def handler(value: object) -> None:
            _alive.discard(signals)
            callback(value)

        return handler

    queued = Qt.ConnectionType.QueuedConnection
    signals.finished.connect(done(on_finished), queued)
    signals.failed.connect(done(on_failed), queued)
    if on_progress:
        signals.progress.connect(on_progress, queued)
    QThreadPool.globalInstance().start(_Task(fn, signals))
