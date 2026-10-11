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
    # líneas que el OCR probablemente leyó mal: {nº de página: nº de líneas}
    ocr_doubts: dict[int, int] = field(default_factory=dict)
    # páginas que fallaron y se sustituyeron por una página en blanco con un aviso
    failed_pages: set[int] = field(default_factory=set)
    attachments_removed: int = 0  # ficheros adjuntos quitados (PDF)
    images_ocr: int = 0  # imágenes sueltas leídas con OCR (y anonimizadas si hacía falta)
    image_leftovers: list[Match] = field(default_factory=list)  # datos que aún se leen
