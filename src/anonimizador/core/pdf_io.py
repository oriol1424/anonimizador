"""Lectura y anonimización de PDF, con BORRADO REAL.

Dos tipos de página:

- **Con texto** (PDF generado desde Word, etc.): se eliminan los caracteres del contenido
  de la página con las redacciones de PyMuPDF (no se tapan: desaparecen), se borran los
  píxeles de imágenes que queden debajo y se escribe el alias en su sitio.
- **Imagen** (escaneada, o con una imagen que cubre la mayor parte): se rasteriza, se lee
  con OCR, se pintan de blanco los píxeles de cada dato y se rehace la página con la
  imagen limpia, el alias visible y una capa de texto invisible ya anonimizada (para poder
  copiar el texto o pasarlo a la IA). Del contenido original de la página no queda nada.

Licencia: PyMuPDF bajo AGPL-3.0 (gratis). Ver docs/LICENCIAS.md.
"""

import threading
from collections import deque
from concurrent.futures import Future, wait
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from anonimizador.core import ocr
from anonimizador.core.matcher import Match, Matcher
from anonimizador.core.progress import PageProgress, Steps
from anonimizador.core.result import ProcessResult

MIN_IMAGE_COVERAGE = 0.5  # imagen que cubre ≥50% de la página -> se trata con OCR
MIN_HORIZONTAL_SCALE = 0.55  # por debajo, además de estrechar se reduce el tamaño de letra
MIN_FONT_SIZE = 5.0
PIXEL_PADDING = 3  # margen al borrar píxeles alrededor de cada dato
JPEG_QUALITY = 80
LOOKAHEAD = 2 * ocr.WORKERS  # páginas imagen cuyo OCR se encola por adelantado
MAX_FIX_ROUNDS = 2  # vueltas de "verificar y volver a borrar" en páginas imagen

Progress = PageProgress  # (páginas hechas, total de páginas) dentro de una fase


class EncryptedPdfError(Exception):
    pass


# Ligaduras tipográficas ("ﬁ", "ﬂ") separadas en letras: si no, "Oﬁcial" o "Griﬀ" no
# coinciden con lo que escribe el usuario. La 1ª letra se queda la caja de la ligadura.
_TEXT_FLAGS = pymupdf.TEXTFLAGS_RAWDICT & ~pymupdf.TEXT_PRESERVE_LIGATURES


@dataclass(frozen=True)
class _Char:
    rect: pymupdf.Rect
    origin: tuple[float, float]
    size: float
    line: int


@dataclass
class _Replacement:
    rects: list[pymupdf.Rect]  # una por línea que ocupa el dato
    origin: tuple[float, float]
    size: float
    width: float
    text: str


def _open(path: Path) -> pymupdf.Document:
    doc = pymupdf.open(str(path))
    if doc.needs_pass:
        doc.close()
        raise EncryptedPdfError(str(path))
    _uncrop(doc)
    return doc


def _uncrop(doc: pymupdf.Document) -> None:
    """Texto fuera del recorte visible (CropBox): no se ve en pantalla, pero sigue en el
    fichero y otras herramientas lo leen. Se trabaja con la página entera (MediaBox) para
    encontrarlo, borrarlo y verificarlo como el resto."""
    for page in doc:
        try:
            if page.cropbox != page.mediabox:
                page.set_cropbox(page.mediabox)
        except Exception:  # noqa: BLE001 - recorte raro: se deja (el resto sigue igual)
            continue


def _remove_attachments(doc: pymupdf.Document) -> int:
    """Ficheros adjuntos (del documento y de anotaciones): su contenido no se revisa, así
    que se quitan. Devuelve cuántos."""
    removed = 0
    for name in doc.embfile_names():
        doc.embfile_del(name)
        removed += 1
    for page in doc:
        attached = [a for a in page.annots() if a.type[0] == pymupdf.PDF_ANNOT_FILE_ATTACHMENT]
        for annot in attached:
            page.delete_annot(annot)
            removed += 1
    return removed


def is_image_page(page: pymupdf.Page) -> bool:
    page_area = abs(page.rect)
    if page_area == 0:
        return False
    covered = sum(abs(pymupdf.Rect(i["bbox"]) & page.rect) for i in page.get_image_info())
    return covered / page_area >= MIN_IMAGE_COVERAGE


def _scanned_count(doc: pymupdf.Document) -> int:
    return sum(1 for page in doc if is_image_page(page))


# --- Páginas con texto ----------------------------------------------------------------


def _page_chars(page: pymupdf.Page) -> tuple[str, list[_Char | None]]:
    """Texto de la página y la caja de cada carácter (None = salto de línea virtual)."""
    pieces: list[str] = []
    chars: list[_Char | None] = []
    line_id = 0
    for block in page.get_text("rawdict", flags=_TEXT_FLAGS)["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for ch in span["chars"]:
                    pieces.append(ch["c"])
                    chars.append(
                        _Char(pymupdf.Rect(ch["bbox"]), ch["origin"], span["size"], line_id)
                    )
            pieces.append("\n")
            chars.append(None)
            line_id += 1
    return "".join(pieces), chars


def _shrink(rect: pymupdf.Rect) -> pymupdf.Rect:
    """Recorta un poco la caja para no tocar las letras vecinas ni las líneas de arriba/abajo."""
    dy = rect.height * 0.2
    dx = min(0.3, rect.width * 0.05)
    return pymupdf.Rect(rect.x0 + dx, rect.y0 + dy, rect.x1 - dx, rect.y1 - dy)


def _rects_by_line(boxes: list[tuple[pymupdf.Rect, int] | None]) -> list[pymupdf.Rect]:
    by_line: dict[int, pymupdf.Rect] = {}
    for box in boxes:
        if box is None or box[0].is_empty:
            continue
        rect, line = box
        by_line[line] = by_line[line] | rect if line in by_line else +rect
    return list(by_line.values())


def _plan(match: Match, chars: list[_Char | None]) -> _Replacement | None:
    span = [c for c in chars[match.start : match.end] if c is not None and not c.rect.is_empty]
    if not span:
        return None
    rects = _rects_by_line([(c.rect, c.line) for c in span])
    return _Replacement(rects, span[0].origin, span[0].size, rects[0].width, match.replacement)


def _write_text(
    page: pymupdf.Page, text: str, origin, size: float, width: float, invisible: bool = False
) -> None:
    """Escribe `text` desde `origin`, estrechándolo si no cabe en `width`."""
    natural = pymupdf.get_text_length(text, fontname="helv", fontsize=size)
    scale = 1.0 if natural <= width or natural == 0 else width / natural
    if scale < MIN_HORIZONTAL_SCALE and not invisible:
        size = max(MIN_FONT_SIZE, size * scale / MIN_HORIZONTAL_SCALE)
        scale = MIN_HORIZONTAL_SCALE
    origin = pymupdf.Point(origin)
    page.insert_text(
        origin, text, fontsize=size, fontname="helv", render_mode=3 if invisible else 0,
        morph=(origin, pymupdf.Matrix(scale, 1)),
    )  # fmt: skip


def _anonymize_text_page(page: pymupdf.Page, matcher: Matcher) -> list[Match]:
    text, chars = _page_chars(page)
    plans, matches = [], []
    for match in matcher.find(text):
        plan = _plan(match, chars)
        if plan:
            plans.append(plan)
            matches.append(match)
    if not plans:
        return []
    for plan in plans:
        for rect in plan.rects:
            page.add_redact_annot(_shrink(rect), fill=False)
    page.apply_redactions(
        images=pymupdf.PDF_REDACT_IMAGE_PIXELS,  # borra también lo que haya debajo
        graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,  # conserva líneas de tablas
        text=pymupdf.PDF_REDACT_TEXT_REMOVE,
    )
    for plan in plans:
        _write_text(page, plan.text, plan.origin, plan.size, plan.width)
    return matches


# --- Páginas imagen (OCR) -------------------------------------------------------------


def _lines_with_replacements(text: str, matches: list[Match]) -> list[str]:
    """Texto por líneas con los alias aplicados, conservando el número de líneas.

    Si un dato ocupa dos líneas, el alias va en la primera y la segunda queda sin él.
    """
    lines, current = [], []
    i, pending = 0, iter(matches)
    nxt = next(pending, None)
    while i < len(text):
        if nxt is not None and i == nxt.start:
            current.append(nxt.replacement)
            for char in text[nxt.start : nxt.end]:
                if char == "\n":
                    lines.append("".join(current))
                    current = []
            i = nxt.end
            nxt = next(pending, None)
            continue
        if text[i] == "\n":
            lines.append("".join(current))
            current = []
        else:
            current.append(text[i])
        i += 1
    if current:
        lines.append("".join(current))
    return lines


def _pad(rect: pymupdf.Rect) -> pymupdf.Rect:
    return pymupdf.Rect(rect.x0 - PIXEL_PADDING, rect.y0 - PIXEL_PADDING,
                        rect.x1 + PIXEL_PADDING, rect.y1 + PIXEL_PADDING)  # fmt: skip


def _erase(
    pix: pymupdf.Pixmap, boxes: list[tuple[pymupdf.Rect, int] | None], matches: list[Match]
) -> list[_Replacement]:
    """Pinta de blanco los píxeles de cada dato y devuelve dónde escribir su alias."""
    to_points = pymupdf.Matrix(72 / ocr.OCR_DPI, 72 / ocr.OCR_DPI)
    image = ocr.pixels(pix)  # pix.set_rect va píxel a píxel desde Python: muy lento
    aliases: list[_Replacement] = []
    for match in matches:
        rects = _rects_by_line(boxes[match.start : match.end])
        if not rects:
            continue
        for rect in rects:
            box = (_pad(rect) & pymupdf.Rect(pix.irect)).irect
            image[box.y0 : box.y1, box.x0 : box.x1] = 255
        first = rects[0] * to_points
        origin = (first.x0, first.y1 - first.height * 0.2)
        aliases.append(
            _Replacement([first], origin, first.height * 0.75, first.width, match.replacement)
        )
    return aliases


def _rebuild_image_page(
    page: pymupdf.Page,
    pix: pymupdf.Pixmap,
    aliases: list[_Replacement],
    result: ocr.OcrPage,
    line_texts: list[str],
) -> None:
    # Se vacía la página por completo (texto, imágenes y dibujos originales)...
    page.add_redact_annot(page.rect)
    page.apply_redactions(
        images=pymupdf.PDF_REDACT_IMAGE_REMOVE,
        graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
        text=pymupdf.PDF_REDACT_TEXT_REMOVE,
    )
    # ...y se rehace con la imagen limpia, los alias y el texto invisible anonimizado.
    page.insert_image(page.rect, stream=pix.tobytes("jpeg", jpg_quality=JPEG_QUALITY))
    for alias in aliases:
        _write_text(page, alias.text, alias.origin, alias.size, alias.width)
    to_points = pymupdf.Matrix(72 / ocr.OCR_DPI, 72 / ocr.OCR_DPI)
    for words, line_text in zip(result.lines, line_texts, strict=False):
        if not line_text.strip():
            continue
        rect = pymupdf.Rect(words[0].rect)
        for word in words[1:]:
            rect |= word.rect
        rect = rect * to_points
        origin = (rect.x0, rect.y1 - rect.height * 0.2)
        _write_text(page, line_text, origin, rect.height * 0.75, rect.width, invisible=True)


@dataclass
class _ScanCheck:
    """Página imagen ya rehecha, a la espera del OCR que la verifica."""

    number: int
    pix: pymupdf.Pixmap
    aliases: list[_Replacement]
    result: ocr.OcrPage
    line_texts: list[str]
    done: list[Match]
    check: Future


def _note_doubts(page: pymupdf.Page, result: ocr.OcrPage, doubts: dict[int, int] | None) -> None:
    if doubts is not None and (count := len(result.doubtful_lines())):
        doubts[page.number + 1] = count


def _start_image_page(
    page: pymupdf.Page, matcher: Matcher, doubts: dict[int, int]
) -> _ScanCheck | None:
    """Borra los datos de una página imagen, la rehace y encola el OCR que la verifica.

    Las páginas sin datos no se verifican: su imagen no cambia y otro OCR no aportaría.
    """
    if page.rotation:
        page.remove_rotation()
    pix = ocr.render(page)
    result = ocr.recognize(pix)
    _note_doubts(page, result, doubts)
    text, boxes = result.text_and_boxes()
    matches = matcher.find(text)
    aliases = _erase(pix, boxes, matches)
    line_texts = _lines_with_replacements(text, matches)
    _rebuild_image_page(page, pix, aliases, result, line_texts)
    if not matches:
        return None
    check = ocr.submit(ocr.render(page))
    return _ScanCheck(page.number, pix, aliases, result, line_texts, list(matches), check)


def _finish_image_page(
    page: pymupdf.Page, state: _ScanCheck, matcher: Matcher
) -> tuple[list[Match], list[Match]]:
    """Si el OCR de la página resultante aún encuentra datos (p. ej. el primer OCR leyó
    mal una línea), se borran también en la imagen y se vuelve a verificar, hasta
    `MAX_FIX_ROUNDS` veces. Devuelve (sustituciones hechas, datos que siguen visibles).
    """
    check = state.check.result()
    for _ in range(MAX_FIX_ROUNDS):
        check_text, check_boxes = check.text_and_boxes()
        leftovers = matcher.find(check_text)
        if not leftovers:
            return state.done, []
        state.aliases += _erase(state.pix, check_boxes, leftovers)
        state.done += leftovers
        _rebuild_image_page(page, state.pix, state.aliases, state.result, state.line_texts)
        check = ocr.recognize(ocr.render(page))
    return state.done, matcher.find(check.text_and_boxes()[0])


class _Prefetch:
    """Encola el OCR de las próximas páginas imagen mientras se procesa la actual.

    Solo `LOOKAHEAD` páginas por delante: cada imagen en cola ocupa ~12 MB.
    """

    def __init__(self, doc: pymupdf.Document):
        self.doc = doc
        self.pages = [page.number for page in doc if is_image_page(page)]
        self.next = 0

    def upto(self, number: int) -> None:
        while self.next < len(self.pages) and self.pages[self.next] <= number + LOOKAHEAD:
            ocr.submit(ocr.render(self.doc[self.pages[self.next]]))
            self.next += 1


def _page_text(page: pymupdf.Page, use_ocr: bool, doubts: dict[int, int] | None = None) -> str:
    """Texto de la página; las páginas imagen se leen con OCR salvo con `use_ocr=False`
    (entonces se devuelve su capa de texto, p. ej. la invisible ya anonimizada)."""
    if use_ocr and is_image_page(page):
        result = ocr.recognize(ocr.render(page))
        _note_doubts(page, result, doubts)
        return result.text_and_boxes()[0]
    return _page_chars(page)[0]


# --- Partes del documento fuera de las páginas ----------------------------------------


def _anonymize_page_extras(page: pymupdf.Page, matcher: Matcher) -> None:
    """Comentarios, campos de formulario y enlaces de la página."""
    for annot in page.annots():
        info = annot.info
        content = matcher.replace(info.get("content", ""))
        annot.set_info(content=content, title="Autor" if info.get("title") else "")
        annot.update()
    for widget in page.widgets():
        if isinstance(widget.field_value, str) and widget.field_value:
            new_value = matcher.replace(widget.field_value)
            if new_value != widget.field_value:
                widget.field_value = new_value
                widget.update()
    for link in page.get_links():
        if link.get("uri"):
            new_uri = matcher.replace(link["uri"])
            if new_uri != link["uri"]:
                link["uri"] = new_uri
                page.update_link(link)


def _anonymize_document_extras(doc: pymupdf.Document, matcher: Matcher) -> None:
    meta = doc.metadata or {}
    doc.set_metadata({
        "title": matcher.replace(meta.get("title") or ""),
        "subject": matcher.replace(meta.get("subject") or ""),
        "keywords": matcher.replace(meta.get("keywords") or ""),
        "author": "",
        "creator": "",
        "producer": "",
    })  # fmt: skip
    doc.del_xml_metadata()
    toc = doc.get_toc(simple=False)
    if toc:
        doc.set_toc([[lvl, matcher.replace(title), page, *rest] for lvl, title, page, *rest in toc])


# --- Páginas que fallan ----------------------------------------------------------------

FAILED_PAGE_TEXT = "[Pàgina {n} no processada]"


def _replace_failed_page(doc: pymupdf.Document, number: int, text: str) -> None:
    """Sustituye una página que no se ha podido procesar por una en blanco con un aviso.

    Nunca se deja la original: podría contener datos sin anonimizar. Se borra y se crea
    de nuevo (y no se vacía con una redacción) porque la página puede estar dañada.
    """
    try:
        rect = doc[number].rect
    except Exception:  # noqa: BLE001 - página ilegible: tamaño A4
        rect = pymupdf.paper_rect("a4")
    doc.delete_page(number)
    page = doc.new_page(number, width=rect.width, height=rect.height)
    page.insert_text((56, 72), text.format(n=number + 1), fontsize=14, fontname="helv")


# --- API ------------------------------------------------------------------------------


def anonymize(
    src: Path,
    dst: Path,
    matcher: Matcher,
    progress: Progress | None = None,
    failed_page_text: str = FAILED_PAGE_TEXT,
) -> ProcessResult:
    """Si una página falla, no se aborta todo: se sustituye por una página en blanco con
    `failed_page_text` ({n} = nº de página) y se anota en `ProcessResult.failed_pages`."""
    doc = _open(src)
    scanned = _scanned_count(doc)
    all_matches: list[Match] = []
    leftovers: list[tuple[int, Match]] = []
    doubts: dict[int, int] = {}
    failed: set[int] = set()
    images = 0
    attachments = _remove_attachments(doc)
    try:
        steps = Steps(progress, doc.page_count)
        prefetch = _Prefetch(doc)
        checks: deque[_ScanCheck] = deque()  # verificaciones en curso (en paralelo)

        def fail(number: int) -> None:
            _replace_failed_page(doc, number, failed_page_text)
            failed.add(number + 1)

        def finish_oldest() -> None:
            state = checks.popleft()
            if state.number + 1 in failed:
                return
            try:
                done, remaining = _finish_image_page(doc[state.number], state, matcher)
            except Exception:  # noqa: BLE001 - cualquier fallo de una página
                fail(state.number)
                return
            all_matches.extend(done)
            leftovers.extend((state.number + 1, m) for m in remaining)

        for number in range(doc.page_count):
            page = doc[number]
            try:
                prefetch.upto(number)
                _anonymize_page_extras(page, matcher)
                if is_image_page(page):
                    state = _start_image_page(page, matcher, doubts)
                    if state is not None:
                        checks.append(state)
                else:
                    page_images = len(page.get_images(full=True))
                    all_matches.extend(_anonymize_text_page(page, matcher))
                    images += page_images
            except Exception:  # noqa: BLE001 - cualquier fallo de una página
                fail(number)
            while len(checks) > ocr.WORKERS:
                finish_oldest()
            steps.tick()
        while checks:
            finish_oldest()
        _anonymize_document_extras(doc, matcher)
        # garbage=4 + clean: no deja copias del contenido antiguo dentro del fichero.
        doc.save(str(dst), garbage=4, deflate=True, clean=True)
    finally:
        doc.close()
    return ProcessResult(all_matches, images, scanned, leftovers, doubts, failed, attachments)


def extract_text(
    path: Path,
    progress: Progress | None = None,
    use_ocr: bool = True,
    doubts: dict[int, int] | None = None,
    failed: set[int] | None = None,
) -> str:
    """Todo el texto susceptible de contener datos (páginas, metadatos, notas, enlaces...).

    Las páginas imagen se leen con OCR. Con `use_ocr=False` se toma su capa de texto: lo
    usa la verificación final, porque `anonymize` ya verificó su imagen con OCR.
    Si se pasa `doubts`, se anota en él {nº de página: líneas dudosas del OCR}.
    Si se pasa `failed`, las páginas que no se pueden leer se saltan y se anotan en él.
    """
    doc = _open(path)
    lines: list[str] = []
    try:
        steps = Steps(progress, doc.page_count)
        prefetch = _Prefetch(doc) if use_ocr else None
        for page in doc:
            try:
                lines.extend(_page_lines(page, use_ocr, prefetch, doubts))
            except Exception:  # noqa: BLE001 - página ilegible: se avisa y se sigue
                if failed is None:
                    raise
                failed.add(page.number + 1)
            steps.tick()
        meta = doc.metadata or {}
        lines.extend(v for k in ("title", "subject", "keywords", "author") if (v := meta.get(k)))
        lines.extend(entry[1] for entry in doc.get_toc())
    finally:
        doc.close()
    return "\n".join(line for line in lines if line)


def _page_lines(
    page: pymupdf.Page,
    use_ocr: bool,
    prefetch: _Prefetch | None,
    doubts: dict[int, int] | None,
) -> list[str]:
    if prefetch:
        prefetch.upto(page.number)
    lines = [_page_text(page, use_ocr, doubts)]
    for annot in page.annots():
        lines.extend(v for v in (annot.info.get("content"), annot.info.get("title")) if v)
    lines.extend(w.field_value for w in page.widgets() if isinstance(w.field_value, str))
    lines.extend(link["uri"] for link in page.get_links() if link.get("uri"))
    return lines


def anonymized_text(
    src: Path,
    matcher: Matcher,
    progress: Progress | None = None,
    failed_page_text: str = FAILED_PAGE_TEXT,
    failed: set[int] | None = None,
) -> str:
    """Texto del PDF ORIGINAL con las sustituciones aplicadas (para exportar a .txt).

    Se parte del original y no del PDF anonimizado porque los alias insertados quedan al
    final del contenido de la página y al extraerlos saldrían fuera de orden.
    """
    doc = _open(src)
    try:
        steps = Steps(progress, doc.page_count)
        prefetch = _Prefetch(doc)
        pages = []
        for page in doc:
            try:
                prefetch.upto(page.number)
                pages.append(matcher.replace(_page_text(page, True)).strip())
            except Exception:  # noqa: BLE001 - como en `anonymize`: nunca el original
                pages.append(failed_page_text.format(n=page.number + 1))
                if failed is not None:
                    failed.add(page.number + 1)
            steps.tick()
        return "\n\n".join(p for p in pages if p).strip() + "\n"
    finally:
        doc.close()


def read_ahead(path: Path, stop: threading.Event) -> None:
    """Lee con OCR las páginas imagen en segundo plano (mientras el usuario rellena la
    lista); el análisis aprovecha después lo ya leído. Se detiene en cuanto `stop` se
    activa: PyMuPDF no admite usarse desde dos hilos a la vez.
    """
    try:
        doc = _open(path)
    except Exception:  # el análisis ya mostrará el error al usuario
        return
    try:
        queued: deque[Future] = deque()
        for page in doc:
            if stop.is_set():
                return
            if not is_image_page(page):
                continue
            queued.append(ocr.submit(ocr.render(page)))
            while len(queued) > LOOKAHEAD and not stop.is_set():
                if wait([queued[0]], timeout=0.2).done:
                    queued.popleft()
    finally:
        doc.close()


def page_counts(path: Path) -> tuple[int, int]:
    """(páginas, páginas escaneadas)."""
    doc = _open(path)
    try:
        return doc.page_count, _scanned_count(doc)
    finally:
        doc.close()
