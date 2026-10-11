"""Ejecuta tareas largas fuera del hilo de la interfaz para que la ventana no se congele."""

import threading
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal

from anonimizador.core.keep_awake import keep_awake
from anonimizador.core.progress import Cancelled, Progress

# Las señales deben vivir hasta que el resultado llegue al hilo de la interfaz; si Python las
# recolecta antes, el aviso se pierde y la ventana se queda "Treballant…" para siempre.
_alive: set["_Signals"] = set()


class _Signals(QObject):
    finished = Signal(object)
    failed = Signal(object)
    cancelled = Signal()
    progress = Signal(str, int, int)


class Task:
    """Tarea en marcha: permite pedir que se cancele."""

    def __init__(self) -> None:
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    @property
    def cancel_requested(self) -> bool:
        return self._cancel.is_set()


class _Runnable(QRunnable):
    def __init__(self, fn: Callable[[Progress], object], signals: _Signals, task: Task):
        super().__init__()
        self.fn = fn
        self.signals = signals
        self.task = task

    def progress(self, phase: str, done: int, total: int) -> None:
        # El núcleo llama aquí a menudo: es el punto donde se atiende la cancelación.
        if self.task.cancel_requested:
            raise Cancelled
        self.signals.progress.emit(phase, done, total)

    def run(self) -> None:
        try:
            with keep_awake():  # que el ordenador no se duerma a media tarea
                result = self.fn(self.progress)
        except Cancelled:
            self.signals.cancelled.emit()
        except Exception as exc:  # se muestra al usuario en la ventana
            self.signals.failed.emit(exc)
        else:
            if self.task.cancel_requested:  # se pidió al final, cuando ya no se podía parar
                self.signals.cancelled.emit()
            else:
                self.signals.finished.emit(result)


def run_in_background(
    fn: Callable[[Progress], object],
    on_finished: Callable[[object], None],
    on_failed: Callable[[Exception], None],
    on_progress: Callable[[str, int, int], None] | None = None,
    on_cancelled: Callable[[], None] | None = None,
) -> Task:
    """Ejecuta `fn(progress)` en otro hilo; las respuestas llegan al hilo de la interfaz.

    `fn` recibe `progress(fase, hecho, total)`; si se cancela la tarea devuelta, la
    siguiente llamada a `progress` detiene `fn` y llega `on_cancelled`.
    """
    signals = _Signals()  # creado aquí -> pertenece al hilo de la interfaz
    _alive.add(signals)
    task = Task()

    def done(callback: Callable[..., None]) -> Callable[..., None]:
        def handler(*value: object) -> None:
            _alive.discard(signals)
            callback(*value)

        return handler

    queued = Qt.ConnectionType.QueuedConnection
    signals.finished.connect(done(on_finished), queued)
    signals.failed.connect(done(on_failed), queued)
    signals.cancelled.connect(done(on_cancelled or (lambda: None)), queued)
    if on_progress:
        signals.progress.connect(on_progress, queued)
    QThreadPool.globalInstance().start(_Runnable(fn, signals, task))
    return task
