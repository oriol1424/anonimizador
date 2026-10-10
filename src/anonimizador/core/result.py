"""Resultado común de anonimizar un fichero, sea Word o PDF."""

from dataclasses import dataclass

from anonimizador.core.matcher import Match


@dataclass
class ProcessResult:
    matches: list[Match]
    images: int  # imágenes u objetos incrustados cuyo contenido no se revisa
    scanned_pages: int = 0  # páginas que son solo imagen (necesitan OCR)
