"""Progreso por fases y cancelación de las tareas largas.

La interfaz recibe `progress(fase, hecho, total)` con un código de fase (no un texto):
- "read": páginas del documento leídas (las escaneadas, con OCR).
- "detect": trozos de texto revisados por el detector de nombres.
- "anonymize": páginas anonimizadas (las escaneadas incluyen su verificación con OCR).
- "verify": páginas del resultado revisadas en la verificación final.
- "export": páginas pasadas a texto (.txt).

Para cancelar, la función de progreso lanza `Cancelled`.
"""

from collections.abc import Callable

Progress = Callable[[str, int, int], None]
PageProgress = Callable[[int, int], None]  # (hecho, total) dentro de una fase

PHASES = ("read", "detect", "anonymize", "verify", "export")


class Cancelled(BaseException):  # noqa: N818 - no es un error: lo pide el usuario
    """El usuario ha cancelado. Hereda de BaseException para que ningún `except
    Exception` (p. ej. el de una página que falla) la confunda con un error."""


def phase(progress: Progress | None, name: str) -> PageProgress | None:
    """Función de progreso de una sola fase."""
    if progress is None:
        return None
    return lambda done, total: progress(name, done, total)


class Steps:
    """Cuenta los pasos de una fase y avisa a la interfaz en cada uno."""

    def __init__(self, progress: PageProgress | None, total: int):
        self.progress = progress
        self.total = total
        self.done = 0
        if progress and total:
            progress(0, total)

    def tick(self) -> None:
        self.done += 1
        if self.progress:
            self.progress(self.done, self.total)
