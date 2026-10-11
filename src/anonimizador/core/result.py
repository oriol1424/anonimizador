"""Resultado común de anonimizar un fichero, sea Word o PDF."""

from dataclasses import dataclass, field

from anonimizador.core.matcher import Match


@dataclass
class ProcessResult:
    matches: list[Match]
    images: int  # imágenes u objetos incrustados cuyo contenido no se revisa
    scanned_pages: int = 0  # páginas que son solo imagen (necesitan OCR)
    # datos que el OCR aún ve en páginas imagen tras borrarlos: (nº de página, dato)
    scan_leftovers: list[tuple[int, Match]] = field(default_factory=list)
