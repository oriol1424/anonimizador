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
