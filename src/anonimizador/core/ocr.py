"""OCR local de páginas escaneadas con RapidOCR (PP-OCRv6, soporta catalán).

- Todo en local: los modelos vienen dentro del paquete `rapidocr`; no se descarga nada.
- Licencias: rapidocr y sus modelos Apache-2.0, onnxruntime MIT (docs/LICENCIAS.md).
- Los resultados se guardan en memoria (nunca en disco) para no repetir el OCR de una
  misma página entre el análisis y la anonimización.
"""

import hashlib
import threading
from collections import OrderedDict
from dataclasses import dataclass

import pymupdf

OCR_DPI = 200
_CACHE_SIZE = 256

_engine = None
_lock = threading.Lock()
_cache: OrderedDict[str, "OcrPage"] = OrderedDict()


@dataclass(frozen=True)
class OcrWord:
    text: str
    rect: pymupdf.Rect  # en píxeles de la imagen


@dataclass(frozen=True)
class OcrPage:
    lines: tuple[tuple[OcrWord, ...], ...]

    def text_and_boxes(self) -> tuple[str, list[tuple[pymupdf.Rect, int] | None]]:
        """Texto de la página y, por carácter, su caja aproximada y su línea.

        RapidOCR da una caja por palabra; la caja de cada letra se estima repartiendo el
        ancho de la palabra a partes iguales (suficiente para "l'Orriols" -> "Orriols").
        """
        pieces: list[str] = []
        boxes: list[tuple[pymupdf.Rect, int] | None] = []
        for line_no, words in enumerate(self.lines):
            for i, word in enumerate(words):
                if i:
                    pieces.append(" ")
                    boxes.append(None)
                width = word.rect.width / max(len(word.text), 1)
                for k, char in enumerate(word.text):
                    x0 = word.rect.x0 + k * width
                    pieces.append(char)
                    boxes.append(
                        (pymupdf.Rect(x0, word.rect.y0, x0 + width, word.rect.y1), line_no)
                    )
            pieces.append("\n")
            boxes.append(None)
        return "".join(pieces), boxes


def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr import RapidOCR  # import diferido: tarda en cargar

        _engine = RapidOCR(
            params={
                "Global.log_level": "warning",
                "Global.return_word_box": True,
                # El clasificador de orientación giraba 180° líneas correctas y las leía
                # mal ("2 a 02s"): un nombre quedaba sin borrar. Las páginas giradas ya se
                # corrigen con /Rotate, así que no aporta nada.
                "Global.use_cls": False,
            }
        )
    return _engine


def _box_rect(points) -> pymupdf.Rect:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return pymupdf.Rect(min(xs), min(ys), max(xs), max(ys))


def render(page: pymupdf.Page) -> pymupdf.Pixmap:
    return page.get_pixmap(dpi=OCR_DPI, colorspace=pymupdf.csRGB, alpha=False)


def recognize(pix: pymupdf.Pixmap) -> OcrPage:
    key = hashlib.sha256(pix.samples_mv).hexdigest()
    with _lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
        result = _get_engine()(pix.tobytes("png"))
        lines: list[tuple[OcrWord, ...]] = []
        for line in result.word_results or ():
            words = tuple(OcrWord(text, _box_rect(box)) for text, _score, box in line if text)
            if words:
                lines.append(words)
        lines.sort(key=lambda ws: (round(ws[0].rect.y0 / 10), ws[0].rect.x0))
        page = OcrPage(tuple(lines))
        _cache[key] = page
        if len(_cache) > _CACHE_SIZE:
            _cache.popitem(last=False)
        return page


def clear_cache() -> None:
    with _lock:
        _cache.clear()
