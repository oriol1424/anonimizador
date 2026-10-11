"""OCR local de páginas escaneadas con RapidOCR (PP-OCRv6, soporta catalán).

- Todo en local: los modelos vienen dentro del paquete `rapidocr`; no se descarga nada.
- Licencias: rapidocr y sus modelos Apache-2.0, onnxruntime MIT (docs/LICENCIAS.md).
- Los resultados se guardan en memoria (nunca en disco) para no repetir el OCR de una
  misma página entre el análisis y la anonimización.
- Se leen `WORKERS` páginas a la vez, cada una en su hilo con su propio motor. Cada motor
  ocupa ~0,5 GB durante el OCR de un A4: con 2 cabe de sobra en un Mac de 8 GB y da
  ~1,2× (medido); con más apenas mejora y gasta mucha más memoria.
"""

import hashlib
import os
import threading
from collections import OrderedDict
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass

import numpy as np
import pymupdf

OCR_DPI = 200
WORKERS = 2 if (os.cpu_count() or 1) >= 4 else 1
_THREADS_PER_WORKER = max(1, (os.cpu_count() or 1) // WORKERS)
_CACHE_SIZE = 256
# Línea dudosa: confianza baja o texto demasiado disperso para su ancho (p. ej. "24 … 025"
# ocupando toda la línea). Medido: líneas bien leídas ≥ 0,967; la mal leída, 0,714.
LOW_LINE_SCORE = 0.90
SPARSE_RATIO = 0.3  # letras por píxel frente a la mediana de la página

_lock = threading.Lock()
_cache: OrderedDict[str, "OcrPage"] = OrderedDict()
_pending: dict[str, Future] = {}
_local = threading.local()
_executor = ThreadPoolExecutor(max_workers=WORKERS, thread_name_prefix="ocr")


@dataclass(frozen=True)
class OcrWord:
    text: str
    rect: pymupdf.Rect  # en píxeles de la imagen


@dataclass(frozen=True)
class OcrPage:
    lines: tuple[tuple[OcrWord, ...], ...]
    scores: tuple[float, ...] = ()  # confianza de cada línea (0–1), si se conoce

    def doubtful_lines(self) -> list[int]:
        """Líneas que el OCR probablemente ha leído mal (para avisar al usuario)."""
        widths = [ws[-1].rect.x1 - ws[0].rect.x0 for ws in self.lines]
        density = [
            sum(len(w.text) for w in ws) / width if width > 0 else 0.0
            for ws, width in zip(self.lines, widths, strict=True)
        ]
        if not self.lines:
            return []
        typical = sorted(density)[len(density) // 2]
        widest = max(widths)
        doubtful = []
        for i in range(len(self.lines)):
            low = i < len(self.scores) and self.scores[i] < LOW_LINE_SCORE
            sparse = widths[i] >= widest / 2 and density[i] < typical * SPARSE_RATIO
            if low or sparse:
                doubtful.append(i)
        return doubtful

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
    """Un motor por hilo: onnxruntime no comparte bien una sesión entre hilos."""
    if getattr(_local, "engine", None) is None:
        from rapidocr import RapidOCR  # import diferido: tarda en cargar

        _local.engine = RapidOCR(
            params={
                "Global.log_level": "warning",
                "Global.return_word_box": True,
                # El clasificador de orientación giraba 180° líneas correctas y las leía
                # mal ("2 a 02s"): un nombre quedaba sin borrar. Las páginas giradas ya se
                # corrigen con /Rotate, así que no aporta nada.
                "Global.use_cls": False,
                "EngineConfig.onnxruntime.intra_op_num_threads": _THREADS_PER_WORKER,
            }
        )
    return _local.engine


def _box_rect(points) -> pymupdf.Rect:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return pymupdf.Rect(min(xs), min(ys), max(xs), max(ys))


def render(page: pymupdf.Page) -> pymupdf.Pixmap:
    return page.get_pixmap(dpi=OCR_DPI, colorspace=pymupdf.csRGB, alpha=False)


def pixels(pix: pymupdf.Pixmap) -> np.ndarray:
    """Vista (sin copia y modificable) de los píxeles RGB: alto × ancho × 3."""
    rows = np.frombuffer(pix.samples_mv, dtype=np.uint8).reshape(pix.height, pix.stride)
    return rows[:, : pix.width * pix.n].reshape(pix.height, pix.width, pix.n)


def _run(key: str, image: np.ndarray) -> "OcrPage":
    try:
        result = _get_engine()(image)
        # Página en blanco: RapidOCR no da textos y `word_results` vale (("", 1.0, None),).
        word_lines = list(result.word_results or ()) if result.txts else []
        scores = list(result.scores or ())
        if len(scores) != len(word_lines):
            scores = [1.0] * len(word_lines)
        lines: list[tuple[tuple[OcrWord, ...], float]] = []
        for line, score in zip(word_lines, scores, strict=True):
            words = tuple(
                OcrWord(item[0], _box_rect(item[2]))
                for item in line
                if len(item) == 3 and item[0] and item[2] is not None
            )
            if words:
                lines.append((words, float(score)))
        lines.sort(key=lambda item: (round(item[0][0].rect.y0 / 10), item[0][0].rect.x0))
        page = OcrPage(tuple(ws for ws, _ in lines), tuple(sc for _, sc in lines))
        with _lock:
            _cache[key] = page
            if len(_cache) > _CACHE_SIZE:
                _cache.popitem(last=False)
        return page
    finally:
        with _lock:
            _pending.pop(key, None)


def submit(pix: pymupdf.Pixmap) -> Future:
    """Encola el OCR de la imagen y devuelve un Future con su `OcrPage`.

    Si ya está leída o encolada, no se repite. La imagen se copia: se puede modificar
    `pix` después sin afectar al OCR.
    """
    key = hashlib.sha256(pix.samples_mv).hexdigest()
    with _lock:
        if key in _cache:
            _cache.move_to_end(key)
            done: Future = Future()
            done.set_result(_cache[key])
            return done
        if key in _pending:
            return _pending[key]
        # En memoria y en BGR, como espera RapidOCR (sin pasar por PNG).
        image = np.ascontiguousarray(pixels(pix)[:, :, ::-1])
        future = _executor.submit(_run, key, image)
        _pending[key] = future
        return future


def recognize(pix: pymupdf.Pixmap) -> OcrPage:
    return submit(pix).result()


def clear_cache() -> None:
    with _lock:
        _cache.clear()
