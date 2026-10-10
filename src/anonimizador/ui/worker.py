"""Ejecuta tareas largas fuera del hilo de la interfaz para que la ventana no se congele."""

from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal

# Las señales deben vivir hasta que el resultado llegue al hilo de la interfaz; si Python las
# recolecta antes, el aviso se pierde y la ventana se queda "Treballant…" para siempre.
_alive: set["_Signals"] = set()


class _Signals(QObject):
    finished = Signal(object)
    failed = Signal(object)


class _Task(QRunnable):
    def __init__(self, fn: Callable[[], object], signals: _Signals):
        super().__init__()
        self.fn = fn
        self.signals = signals

    def run(self) -> None:
        try:
            result = self.fn()
        except Exception as exc:  # se muestra al usuario en la ventana
            self.signals.failed.emit(exc)
        else:
            self.signals.finished.emit(result)


def run_in_background(
    fn: Callable[[], object],
    on_finished: Callable[[object], None],
    on_failed: Callable[[Exception], None],
) -> None:
    """Ejecuta `fn` en otro hilo y llama a `on_finished`/`on_failed` en el hilo de la interfaz."""
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
    QThreadPool.globalInstance().start(_Task(fn, signals))
