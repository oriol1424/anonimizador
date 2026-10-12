"""Estimación del tiempo de cada fase, antes de empezar.

Segundos medidos en el PC de desarrollo (i7-1065G7, 4 núcleos; docs/PROGRESO.md). En otros
equipos la interfaz corrige la estimación con la velocidad real que va viendo, así que
basta con que las proporciones entre fases sean razonables.
"""

from dataclasses import dataclass

CHARS_PER_PAGE = 1700  # página típica de un escrito

# Segundos por unidad.
READ_TEXT_PAGE = 0.03  # leer el texto de una página PDF
OCR_PAGE = 4.0  # OCR de una página escaneada
OCR_IMAGE = 1.5  # OCR de una imagen suelta (Word o PDF)
DETECT_PER_1000_CHARS = 0.17  # detector de nombres (pesos uint8: ~1,7x el int8 anterior)
ANON_TEXT_PAGE = 0.15  # anonimizar una página PDF con texto
ANON_SCAN_PAGE = 3.8  # rehacer y verificar una página escaneada
ANON_IMAGE = 1.0  # imagen suelta: borrar + verificar (si tiene datos)
ANON_WORD_PER_1000_CHARS = 0.035
VERIFY_PAGE = 0.02
EXPORT_PAGE = 0.05


@dataclass(frozen=True)
class Workload:
    """Lo que hay que procesar (de `pipeline.document_info`)."""

    kind: str  # "docx" o "pdf"
    pages: int = 0  # PDF
    scanned: int = 0  # PDF: páginas escaneadas
    images: int = 0  # imágenes sueltas que se leerán con OCR
    chars: int = 0  # Word: caracteres del texto

    @property
    def text_chars(self) -> int:
        return self.chars if self.kind == "docx" else self.pages * CHARS_PER_PAGE


def analysis(work: Workload, ner: bool = True) -> dict[str, float]:
    """Segundos por fase del análisis ("read", "detect")."""
    read = work.images * OCR_IMAGE
    if work.kind == "pdf":
        read += (work.pages - work.scanned) * READ_TEXT_PAGE + work.scanned * OCR_PAGE
    detect = work.text_chars / 1000 * DETECT_PER_1000_CHARS if ner else 0.0
    return {"read": max(read, 0.2), "detect": max(detect, 0.2)}


def anonymization(work: Workload, output_suffix: str) -> dict[str, float]:
    """Segundos por fase de la anonimización ("anonymize", "verify", "export")."""
    if work.kind == "pdf":
        text_pages = work.pages - work.scanned
        phases = {
            "anonymize": text_pages * ANON_TEXT_PAGE + work.scanned * ANON_SCAN_PAGE
            + work.images * ANON_IMAGE,
            "verify": work.pages * VERIFY_PAGE,
        }  # fmt: skip
        if output_suffix in (".txt", ".md"):
            phases["export"] = work.pages * EXPORT_PAGE
    else:
        phases = {
            "anonymize": work.chars / 1000 * ANON_WORD_PER_1000_CHARS + work.images * ANON_IMAGE,
            "verify": work.images * OCR_IMAGE * 0.3 + work.chars / 1000 * 0.01,
        }
    return {k: max(v, 0.2) for k, v in phases.items()}


def total(work: Workload, output_suffix: str = ".docx", ner: bool = True) -> float:
    return sum(analysis(work, ner).values()) + sum(anonymization(work, output_suffix).values())
