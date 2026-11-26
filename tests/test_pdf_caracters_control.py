"""PDF cuyo texto sale con caracteres de control (fuentes sin tabla Unicode).

Caso del Mac del bufete (2026-11-18): la guía fallaba al escribir esos caracteres en
Word. Revisando el arreglo se vio algo peor: con los espacios leídos como "\x03",
«Joan\x03Puig» no coincidía con la lista y el nombre se quedaba sin anonimizar."""

from pathlib import Path

import pymupdf
import pytest

from anonimizador.core import pdf_io
from anonimizador.core.guide import default_path
from anonimizador.core.lang import CATALAN
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import analyze, anonymize
from anonimizador.core.text import clean_text

TERMS = [Term("Joan Puig i Ferrer", "[CLIENT_1]"), Term("Pere Mas", "[PART_1]")]


def _raw_pdf(path: Path, content: bytes) -> Path:
    """PDF escrito a mano: Helvetica sin ToUnicode; los códigos 0-31 salen tal cual."""
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.7\n")
    offsets = []
    for n, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    path.write_bytes(bytes(out))
    return path


@pytest.fixture
def control_pdf(tmp_path: Path) -> Path:
    text = (
        b"BT /F1 12 Tf 72 760 Td (Demandant:\x03Joan\x03Puig\x03i\x03Ferrer) Tj "
        b"0 -20 Td (i\x03el\x03Sr.\x03Pere\x03Mas,\x03DNI\x0312345678Z.) Tj "
        b"0 -20 Td (Codis:\x00\x01\x0b\x1f.) Tj ET"
    )
    return _raw_pdf(tmp_path / "control.pdf", text)


def test_the_synthetic_pdf_really_has_control_characters(control_pdf: Path):
    doc = pymupdf.open(str(control_pdf))
    raw = "".join(c["c"] for b in doc[0].get_text("rawdict")["blocks"] for line in b["lines"]
                  for s in line["spans"] for c in s["chars"])  # fmt: skip
    doc.close()
    assert "Joan\x03Puig" in raw  # si MuPDF cambia, este test ya no prueba nada


def test_clean_text_keeps_length():
    text = "A\x00B\x03C\x0bD\x1fE\ud800F\ufffeG\tH\nI"
    cleaned = clean_text(text)
    assert len(cleaned) == len(text)
    assert cleaned == "A B C D E\ufffdF\ufffdG\tH\nI"


def test_names_with_control_spaces_are_anonymized(control_pdf: Path, tmp_path: Path):
    out = tmp_path / "sortida.pdf"
    report = anonymize(control_pdf, out, TERMS, guide=default_path(out, CATALAN), language=CATALAN)
    text = pdf_io.extract_text(out)
    for leak in ("Joan", "Puig", "Ferrer", "Pere", "Mas"):
        assert leak not in text, leak
    assert report.replaced["[CLIENT_1]"] >= 1 and report.replaced["[PART_1]"] >= 1
    assert report.guide.exists()


@pytest.mark.parametrize("suffix", [".txt", ".md"])
def test_text_outputs_have_no_control_characters(control_pdf: Path, tmp_path: Path, suffix):
    out = tmp_path / f"sortida{suffix}"
    anonymize(control_pdf, out, TERMS)
    text = out.read_text(encoding="utf-8")
    assert "Joan" not in text and "Mas" not in text
    assert not any(ord(c) < 32 and c not in "\t\n\r" for c in text)


def test_analysis_suggests_clean_forms(control_pdf: Path):
    analysis = analyze(control_pdf, [])
    forms = [f for s in analysis.suggestions for f in s.forms]
    assert any("12345678Z" in f for f in forms)
    assert not any(any(ord(c) < 32 for c in f) for f in forms)


# --- Texto ilegible: fuente sin tabla Unicode («Demandant» se extrae como «%FNBOEBOU») ---

LINES = [
    "Demandant: Joan Puig i Ferrer, amb passaport O1234567.",
    "Demandat: el Sr. Pere Mas, veí d'Andorra la Vella.",
    "Els fets es van produir el mes de febrer.",
]


def _identity_pdf(path: Path, to_unicode: bool) -> Path:
    """Fuente CID (Identity-H) incrustada; sin ToUnicode el texto extraído es basura."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_font(fontname="T0", fontbuffer=pymupdf.Font("tiro").buffer)
    for n, line in enumerate(LINES):
        page.insert_text((72, 100 + 20 * n), line, fontname="T0", fontsize=12)
    if not to_unicode:
        for xref in range(1, doc.xref_length()):
            if doc.xref_get_key(xref, "ToUnicode")[0] != "null":
                doc.xref_set_key(xref, "ToUnicode", "null")
    doc.save(str(path))
    doc.close()
    return path


def test_the_broken_pdf_really_hides_the_names(tmp_path: Path):
    doc = pymupdf.open(str(_identity_pdf(tmp_path / "b.pdf", to_unicode=False)))
    text = doc[0].get_text()
    doc.close()
    assert "Joan" not in text and "Demandant" not in text  # si MuPDF cambia, revisar


def test_broken_text_page_is_read_with_ocr(tmp_path: Path):
    broken = pymupdf.open(str(_identity_pdf(tmp_path / "b.pdf", to_unicode=False)))
    good = pymupdf.open(str(_identity_pdf(tmp_path / "g.pdf", to_unicode=True)))
    assert pdf_io.has_broken_text(broken[0]) and pdf_io.is_image_page(broken[0])
    assert not pdf_io.has_broken_text(good[0]) and not pdf_io.is_image_page(good[0])
    broken.close()
    good.close()


def test_normal_pdf_is_not_flagged(demanda_pdf: Path):
    doc = pymupdf.open(str(demanda_pdf))
    assert not any(pdf_io.has_broken_text(page) for page in doc)
    doc.close()


def test_broken_text_pdf_is_anonymized_and_garbage_removed(tmp_path: Path):
    """Antes: la lista no encontraba nada y el texto desordenado (descifrable por una IA)
    se quedaba en el PDF de salida."""
    src = _identity_pdf(tmp_path / "b.pdf", to_unicode=False)
    out = tmp_path / "sortida.pdf"
    report = anonymize(src, out, TERMS)
    assert report.replaced["[CLIENT_1]"] >= 1 and report.replaced["[PART_1]"] >= 1
    assert any(n.kind == "ocr" for n in report.notices)
    doc = pymupdf.open(str(out))
    text = doc[0].get_text()
    fonts = doc[0].get_fonts()
    doc.close()
    assert "Joan" not in text and "Mas" not in text
    assert "%FNBOEBOU" not in text  # la capa de texto antigua ha desaparecido
    assert "Demandant" in text  # la nueva es legible (OCR)
    assert not any(f[2] == "Type0" for f in fonts)


def test_broken_text_pdf_analysis_finds_the_names(tmp_path: Path):
    src = _identity_pdf(tmp_path / "b.pdf", to_unicode=False)
    forms = [f for s in analyze(src, []).suggestions for f in s.forms]
    assert any("O1234567" in f for f in forms)  # el pasaporte, leído con OCR


# --- Casos de la revisión del crítico (2026-11-26) ---------------------------------------


def _two_font_pdf(path: Path, content: bytes, font2: bytes) -> Path:
    """Como `_raw_pdf`, con una segunda fuente /F2."""
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        font2,
    ]
    out = bytearray(b"%PDF-1.7\n")
    offsets = []
    for n, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    path.write_bytes(bytes(out))
    return path


NAME = "Joan Puig i Ferrer"
# Fuente simple con nombres de glifo inventados (/g12...), como en los subconjuntos.
CUSTOM = (
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding << /Type /Encoding "
    b"/Differences [33 " + b" ".join(b"/g%d" % n for n in range(40)) + b"] >> >>"
)


def _coded(text: str) -> bytes:
    """Cada letra distinta con un código desde 33 (las de /g0, /g1...), como cadena
    hexadecimal del PDF (algún código sería «(» o «)»)."""
    letters = sorted(set(text))
    return b"<" + bytes(33 + letters.index(c) for c in text).hex().encode() + b">"


def _page(path: Path) -> pymupdf.Page:
    return pymupdf.open(str(path))[0]


def test_one_broken_line_in_a_full_page_is_detected(tmp_path: Path):
    """Antes se medía el % de toda la página: un bloque roto se perdía entre el resto."""
    normal = b"".join(b"(Linia normal numero %d del document.) Tj 0 -14 Td " % n for n in range(40))
    content = b"BT /F1 10 Tf 72 800 Td " + normal + b"/F2 10 Tf " + _coded(NAME) + b" Tj ET"
    assert pdf_io.has_broken_text(_page(_two_font_pdf(tmp_path / "m.pdf", content, CUSTOM)))


def test_custom_glyph_names_are_detected(tmp_path: Path):
    content = b"BT /F2 12 Tf 72 760 Td " + _coded(NAME) + b" Tj ET"
    assert pdf_io.has_broken_text(_page(_two_font_pdf(tmp_path / "c.pdf", content, CUSTOM)))


@pytest.mark.parametrize("code", [0x1C, 0x1D, 0x1E, 0x1F])
def test_controls_that_python_treats_as_spaces_count(tmp_path: Path, code: int):
    sep = bytes([code])
    content = b"BT /F1 12 Tf 72 760 Td (Joan" + sep + b"Puig" + sep + b"i" + sep + b"Ferrer) Tj ET"
    assert pdf_io.has_broken_text(_page(_raw_pdf(tmp_path / "x.pdf", content)))


def test_unused_broken_font_does_not_send_page_to_ocr(tmp_path: Path):
    """Una fuente rota declarada en la página pero sin usar: antes todo iba al OCR."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_font(fontname="T0", fontbuffer=pymupdf.Font("tiro").buffer)
    page.insert_text((72, 100), "Demandant: Joan Puig i Ferrer.", fontname="helv")
    for xref in range(1, doc.xref_length()):
        if doc.xref_get_key(xref, "ToUnicode")[0] != "null":
            doc.xref_set_key(xref, "ToUnicode", "null")
    doc.save(str(tmp_path / "u.pdf"))
    assert not pdf_io.is_image_page(_page(tmp_path / "u.pdf"))


def test_single_odd_symbol_is_not_broken_text(tmp_path: Path):
    content = (
        b"BT /F1 12 Tf 72 760 Td (Demandant: Joan Puig i Ferrer, vei d'Andorra.) Tj "
        b"0 -20 Td (Pagina 3 \x01) Tj ET"
    )
    assert not pdf_io.has_broken_text(_page(_raw_pdf(tmp_path / "s.pdf", content)))


def test_corpus_pdfs_are_not_flagged():
    corpus = Path(__file__).parent / "corpus"
    for pdf in corpus.glob("*.pdf"):
        doc = pymupdf.open(str(pdf))
        assert not any(pdf_io.has_broken_text(p) for p in doc), pdf.name
        doc.close()


def test_custom_glyph_names_pdf_is_anonymized(tmp_path: Path):
    """De extremo a extremo: el nombre (en el texto se ve) desaparece de la salida, leída
    también con OCR."""
    from anonimizador.core import ocr

    content = b"BT /F2 14 Tf 72 760 Td " + _coded(NAME) + b" Tj ET"
    src = _two_font_pdf(tmp_path / "c.pdf", content, CUSTOM)
    out = tmp_path / "sortida.pdf"
    anonymize(src, out, TERMS)
    doc = pymupdf.open(str(out))
    seen = " ".join(w.text for ws in ocr.recognize(ocr.render(doc[0])).lines for w in ws)
    doc.close()
    assert "Puig" not in seen and "Joan" not in seen
