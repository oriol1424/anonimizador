"""Imágenes dentro de los documentos (un DNI escaneado pegado en un Word, una firma con
nombre en un PDF): se leen con OCR y se borran los datos encontrados.

Las páginas escaneadas enteras las trata `pdf_io`; aquí van las imágenes sueltas.
"""

from dataclasses import dataclass

import pymupdf

from anonimizador.core import ocr
from anonimizador.core.matcher import Match, Matcher

MIN_SIDE = 40  # px: iconos, viñetas y líneas decorativas no se leen
MIN_AREA = 40_000  # px²
OCR_TARGET = 1600  # px del lado mayor: las imágenes pequeñas se amplían para leerlas bien
MAX_UPSCALE = 3.0
PADDING = 3
MAX_FIX_ROUNDS = 2
ENCODABLE = {"png", "jpg", "jpeg"}  # formatos que se pueden volver a guardar igual


Boxes = list[tuple[pymupdf.Rect, int] | None]


@dataclass
class ImageResult:
    data: bytes | None  # imagen nueva, o None si no había nada que borrar
    matches: list[Match]
    leftovers: list[Match]  # lo que el OCR aún ve tras borrar


def load(data: bytes) -> pymupdf.Pixmap | None:
    """Imagen en RGB sin transparencia, o None si el formato no se puede leer (EMF...)."""
    try:
        pix = pymupdf.Pixmap(data)
    except Exception:  # noqa: BLE001 - formato no admitido
        return None
    return rgb(pix)


def rgb(pix: pymupdf.Pixmap) -> pymupdf.Pixmap:
    if pix.alpha:
        pix = pymupdf.Pixmap(pix, 0)
    if pix.colorspace is None or pix.colorspace.n != 3:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    return pix


def worth_reading(pix: pymupdf.Pixmap) -> bool:
    return min(pix.width, pix.height) >= MIN_SIDE and pix.width * pix.height >= MIN_AREA


def for_ocr(pix: pymupdf.Pixmap) -> pymupdf.Pixmap:
    """Amplía las imágenes pequeñas: el OCR lee mal las letras de pocos píxeles."""
    scale = min(MAX_UPSCALE, OCR_TARGET / max(pix.width, pix.height))
    if scale <= 1.05:
        return pix
    return pymupdf.Pixmap(pix, int(pix.width * scale), int(pix.height * scale), None)


def read(pix: pymupdf.Pixmap) -> tuple[str, Boxes]:
    return ocr.recognize(pix).text_and_boxes()


def rects_by_line(boxes: Boxes) -> list[pymupdf.Rect]:
    by_line: dict[int, pymupdf.Rect] = {}
    for box in boxes:
        if box is None or box[0].is_empty:
            continue
        rect, line = box
        by_line[line] = by_line[line] | rect if line in by_line else +rect
    return list(by_line.values())


def _erase(pix: pymupdf.Pixmap, boxes: Boxes, matches: list[Match]) -> list[tuple]:
    """Pinta de blanco cada dato; devuelve (texto del alias, caja) para escribirlo."""
    image = ocr.pixels(pix)
    aliases = []
    for match in matches:
        rects = rects_by_line(boxes[match.start : match.end])
        for rect in rects:
            box = (pymupdf.Rect(rect.x0 - PADDING, rect.y0 - PADDING, rect.x1 + PADDING,
                                rect.y1 + PADDING) & pymupdf.Rect(pix.irect)).irect  # fmt: skip
            image[box.y0 : box.y1, box.x0 : box.x1] = 255
        if rects:
            aliases.append((match.replacement, rects[0]))
    return aliases


def _with_aliases(pix: pymupdf.Pixmap, aliases: list[tuple]) -> pymupdf.Pixmap:
    """Escribe los alias sobre la imagen (en una página del mismo tamaño en píxeles)."""
    doc = pymupdf.open()
    page = doc.new_page(width=pix.width, height=pix.height)
    page.insert_image(page.rect, pixmap=pix)
    for text, rect in aliases:
        size = max(6.0, rect.height * 0.75)
        natural = pymupdf.get_text_length(text, fontname="helv", fontsize=size)
        scale = min(1.0, rect.width / natural) if natural else 1.0
        origin = pymupdf.Point(rect.x0, rect.y1 - rect.height * 0.2)
        page.insert_text(origin, text, fontsize=size, fontname="helv",
                         morph=(origin, pymupdf.Matrix(max(scale, 0.5), 1)))  # fmt: skip
    return page.get_pixmap(dpi=72, alpha=False)


def anonymize(data: bytes, kind: str, matcher: Matcher) -> ImageResult:
    """Borra de la imagen los datos que encuentra el OCR y la verifica con otro OCR.

    `kind`: extensión ("png", "jpeg"...). Si el formato no se puede volver a guardar igual
    y hay datos, no se cambia y se devuelven como `leftovers` para avisar.
    """
    pix = load(data)
    if pix is None or not worth_reading(pix):
        return ImageResult(None, [], [])
    work = for_ocr(pix)
    if work is pix:
        work = pymupdf.Pixmap(pix)  # copia: se pinta encima
    text, boxes = read(work)
    found = matcher.find(text)
    if not found:
        return ImageResult(None, [], [])
    if kind.lower() not in ENCODABLE:
        return ImageResult(None, [], found)
    done = list(found)
    aliases = _erase(work, boxes, found)
    result = _with_aliases(work, aliases)
    leftovers: list[Match] = []
    for _ in range(MAX_FIX_ROUNDS):
        check_text, check_boxes = read(result)
        leftovers = matcher.find(check_text)
        if not leftovers:
            break
        done += leftovers
        aliases += _erase(work, check_boxes, leftovers)
        result = _with_aliases(work, aliases)
    else:
        leftovers = matcher.find(read(result)[0])
    if kind.lower() == "png":
        encoded = result.tobytes("png")
    else:
        encoded = result.tobytes("jpeg", jpg_quality=88)
    return ImageResult(encoded, done, leftovers)


def text_of(data: bytes) -> str:
    """Texto de una imagen para el análisis y la verificación ("" si no se lee)."""
    pix = load(data)
    if pix is None or not worth_reading(pix):
        return ""
    return read(for_ocr(pix))[0]
