"""Lectura y anonimización de PDF con texto, con BORRADO REAL.

No se dibuja un recuadro encima del nombre (el texto seguiría ahí y se podría copiar):
se eliminan los caracteres del contenido de la página con las redacciones de PyMuPDF,
se borran los píxeles de las imágenes que queden debajo y después se escribe el alias.

Las páginas escaneadas (solo imagen) se detectan y se informan: necesitan OCR.

Licencia: PyMuPDF es AGPL-3.0 o comercial (Artifex). Ver docs/DECISIONES.md.
"""

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from anonimizador.core.matcher import Match, Matcher
from anonimizador.core.result import ProcessResult

MIN_TEXT_CHARS = 20  # menos texto que esto + imagen grande = página escaneada
MIN_IMAGE_COVERAGE = 0.5
MIN_HORIZONTAL_SCALE = 0.55  # por debajo, además de estrechar se reduce el tamaño de letra
MIN_FONT_SIZE = 5.0


class EncryptedPdfError(Exception):
    pass


@dataclass(frozen=True)
class _Char:
    rect: pymupdf.Rect
    origin: tuple[float, float]
    size: float
    line: int


def _open(path: Path) -> pymupdf.Document:
    doc = pymupdf.open(str(path))
    if doc.needs_pass:
        doc.close()
        raise EncryptedPdfError(str(path))
    return doc


def _page_chars(page: pymupdf.Page) -> tuple[str, list[_Char | None]]:
    """Texto de la página y la caja de cada carácter (None = salto de línea virtual)."""
    pieces: list[str] = []
    chars: list[_Char | None] = []
    line_id = 0
    for block in page.get_text("rawdict")["blocks"]:
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


def _is_scanned(page: pymupdf.Page, text: str) -> bool:
    if len(text.strip()) >= MIN_TEXT_CHARS:
        return False
    page_area = abs(page.rect)
    covered = sum(abs(pymupdf.Rect(i["bbox"]) & page.rect) for i in page.get_image_info())
    return page_area > 0 and covered / page_area >= MIN_IMAGE_COVERAGE


def _shrink(rect: pymupdf.Rect) -> pymupdf.Rect:
    """Recorta un poco la caja para no tocar las letras vecinas ni las líneas de arriba/abajo."""
    dy = rect.height * 0.2
    dx = min(0.3, rect.width * 0.05)
    return pymupdf.Rect(rect.x0 + dx, rect.y0 + dy, rect.x1 - dx, rect.y1 - dy)


@dataclass
class _Replacement:
    rects: list[pymupdf.Rect]  # una por línea que ocupa el nombre
    origin: tuple[float, float]
    size: float
    width: float
    text: str


def _plan(match: Match, chars: list[_Char | None]) -> _Replacement | None:
    by_line: dict[int, pymupdf.Rect] = {}
    first: _Char | None = None
    for ch in chars[match.start : match.end]:
        if ch is None or ch.rect.is_empty:
            continue
        first = first or ch
        by_line[ch.line] = by_line[ch.line] | ch.rect if ch.line in by_line else +ch.rect
    if first is None:
        return None
    rects = list(by_line.values())
    return _Replacement(rects, first.origin, first.size, rects[0].width, match.replacement)


def _write_alias(page: pymupdf.Page, r: _Replacement) -> None:
    """Escribe el alias donde estaba el nombre, estrechándolo si no cabe."""
    size = r.size
    natural = pymupdf.get_text_length(r.text, fontname="helv", fontsize=size)
    scale = 1.0 if natural <= r.width or natural == 0 else r.width / natural
    if scale < MIN_HORIZONTAL_SCALE:
        size = max(MIN_FONT_SIZE, size * scale / MIN_HORIZONTAL_SCALE)
        scale = MIN_HORIZONTAL_SCALE
    origin = pymupdf.Point(r.origin)
    page.insert_text(
        origin, r.text, fontsize=size, fontname="helv",
        morph=(origin, pymupdf.Matrix(scale, 1)),
    )  # fmt: skip


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


def anonymize(src: Path, dst: Path, matcher: Matcher) -> ProcessResult:
    doc = _open(src)
    all_matches: list[Match] = []
    scanned = 0
    images = doc.embfile_count()
    try:
        for page in doc:
            text, chars = _page_chars(page)
            images += len(page.get_images(full=True))
            if _is_scanned(page, text):
                scanned += 1
                continue
            _anonymize_page_extras(page, matcher)
            plans = []
            for match in matcher.find(text):
                plan = _plan(match, chars)
                if plan:
                    plans.append(plan)
                    all_matches.append(match)
            for plan in plans:
                for rect in plan.rects:
                    page.add_redact_annot(_shrink(rect), fill=False)
            if plans:
                page.apply_redactions(
                    images=pymupdf.PDF_REDACT_IMAGE_PIXELS,  # borra también lo que haya debajo
                    graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,  # conserva líneas de tablas
                    text=pymupdf.PDF_REDACT_TEXT_REMOVE,
                )
                for plan in plans:
                    _write_alias(page, plan)
        _anonymize_document_extras(doc, matcher)
        # garbage=4 + clean: no deja copias del contenido antiguo dentro del fichero.
        doc.save(str(dst), garbage=4, deflate=True, clean=True)
    finally:
        doc.close()
    return ProcessResult(all_matches, images, scanned)


def extract_text(path: Path) -> str:
    """Todo el texto susceptible de contener datos (páginas, metadatos, notas, enlaces...)."""
    doc = _open(path)
    lines: list[str] = []
    try:
        for page in doc:
            lines.append(_page_chars(page)[0])
            for annot in page.annots():
                lines.extend(v for v in (annot.info.get("content"), annot.info.get("title")) if v)
            lines.extend(w.field_value for w in page.widgets() if isinstance(w.field_value, str))
            lines.extend(link["uri"] for link in page.get_links() if link.get("uri"))
        meta = doc.metadata or {}
        lines.extend(v for k in ("title", "subject", "keywords", "author") if (v := meta.get(k)))
        lines.extend(entry[1] for entry in doc.get_toc())
    finally:
        doc.close()
    return "\n".join(line for line in lines if line)


def anonymized_text(src: Path, matcher: Matcher) -> str:
    """Texto del PDF ORIGINAL con las sustituciones aplicadas (para exportar a .txt).

    Se parte del original y no del PDF anonimizado porque los alias insertados quedan al
    final del contenido de la página y al extraerlos saldrían fuera de orden.
    Las páginas escaneadas se omiten (no tienen texto que anonimizar).
    """
    doc = _open(src)
    try:
        pages = []
        for page in doc:
            text, _ = _page_chars(page)
            if not _is_scanned(page, text):
                pages.append(matcher.replace(text).strip())
        return "\n\n".join(pages).strip() + "\n"
    finally:
        doc.close()


def scanned_pages(path: Path) -> int:
    doc = _open(path)
    try:
        return sum(1 for page in doc if _is_scanned(page, page.get_text()))
    finally:
        doc.close()
