"""Documento largo (80 págs Word, 40 págs PDF) de principio a fin. Lento: `pytest -m slow`."""

import re
import zipfile
from pathlib import Path

import pymupdf
import pytest
from docx import Document

from anonimizador.core import pdf_io
from anonimizador.core.lang import CATALAN
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import analyze, anonymize

pytestmark = pytest.mark.slow

FIRST = ["Jordi", "Núria", "Pere", "Laia", "Marc", "Anna", "Oriol", "Marta", "Pau", "Clara"]
LAST = ["Casals", "Ferrer", "Puig", "Vila", "Soler", "Roca", "Pons", "Serra", "Mas", "Font"]


def _paragraph(i: int) -> str:
    person = f"{FIRST[i % 10]} {LAST[(i * 3) % 10]} i {LAST[(i * 7) % 10]}"
    return (
        f"{i}. En {person}, amb passaport O{1000000 + i} i domicili a l'Avinguda Meritxell, "
        f"{i % 90 + 1}, AD500 Andorra la Vella, va declarar que el Sr. Joan Puig i Ferrer li "
        f"devia 1.500 euros. La societat Esquís Pirineu SL ho va reconèixer davant la Batllia."
    )


def _check(src: Path, out: Path, read) -> None:
    terms = [Term("Joan Puig i Ferrer", "[CLIENT_1]")]
    for suggestion in analyze(src, terms, CATALAN).suggestions:
        terms.extend(suggestion.to_terms())
    report = anonymize(src, out, terms)
    text = read(out)
    assert not [n for n in report.notices if n.is_serious]
    assert not re.search(r"O1\d{6}", text)  # ningún pasaporte
    assert "Joan" not in text and "Meritxell" not in text
    assert "Batllia" in text


def test_long_word(tmp_path):
    src = tmp_path / "llarg.docx"
    doc = Document()
    for i in range(80 * 6):
        doc.add_paragraph(_paragraph(i))
    doc.save(str(src))

    def read(path: Path) -> str:
        with zipfile.ZipFile(path) as z:
            return z.read("word/document.xml").decode("utf-8")

    _check(src, tmp_path / "sortida.docx", read)


def test_long_pdf(tmp_path):
    src = tmp_path / "llarg.pdf"
    doc = pymupdf.open()
    for p in range(40):
        text = "\n\n".join(_paragraph(p * 6 + k) for k in range(6))
        doc.new_page().insert_textbox(pymupdf.Rect(56, 56, 540, 800), text, fontsize=10)
    doc.save(str(src))
    _check(src, tmp_path / "sortida.pdf", pdf_io.extract_text)
