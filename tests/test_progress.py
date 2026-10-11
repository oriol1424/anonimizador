"""Progreso por fases y cancelación (lo que usa la pantalla de progreso de la interfaz)."""

from pathlib import Path

import pymupdf
import pytest

from anonimizador.core import ner
from anonimizador.core.lang import CATALAN
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import analyze, anonymize
from anonimizador.core.progress import Cancelled

TERMS = [Term("Joan Puig i Ferrer", "[CLIENT_1]")]


def _pdf(path: Path, pages: int = 3) -> Path:
    doc = pymupdf.open()
    for n in range(pages):
        doc.new_page().insert_text((56, 72), f"Pàgina {n + 1}: en Joan Puig i Ferrer signa.")
    doc.save(str(path))
    return path


def _record():
    events: list[tuple[str, int, int]] = []
    return events, lambda phase, done, total: events.append((phase, done, total))


def test_analysis_reports_reading_pages(tmp_path):
    events, progress = _record()
    analyze(_pdf(tmp_path / "doc.pdf"), [], CATALAN, progress)
    reads = [e for e in events if e[0] == "read"]
    assert reads == [("read", n, 3) for n in range(4)]
    if ner.is_available():
        detect = [e for e in events if e[0] == "detect"]
        assert detect and detect[-1][1] == detect[-1][2]
        assert events.index(reads[-1]) < events.index(detect[0])  # en orden


def test_anonymize_reports_phases_in_order(tmp_path):
    events, progress = _record()
    anonymize(_pdf(tmp_path / "doc.pdf"), tmp_path / "out.txt", TERMS, progress)
    phases = list(dict.fromkeys(e[0] for e in events))
    assert phases == ["anonymize", "verify", "export"]
    assert ("anonymize", 3, 3) in events and ("export", 3, 3) in events


@pytest.mark.parametrize("phase", ["anonymize", "verify", "export"])
def test_cancel_leaves_no_output(tmp_path, phase):
    src = _pdf(tmp_path / "doc.pdf")
    out = tmp_path / "out.txt"

    def progress(current, done, total):
        if current == phase and done == 1:
            raise Cancelled

    with pytest.raises(Cancelled):
        anonymize(src, out, TERMS, progress)
    assert not out.exists()
    assert not list(tmp_path.glob("out*"))  # tampoco el temporal .tmp.pdf


def test_cancel_is_not_taken_for_a_failed_page(tmp_path):
    """La protección de páginas que fallan (except Exception) no debe tragarse la
    cancelación ni convertirla en una página «no processada»."""
    src = _pdf(tmp_path / "doc.pdf")

    def progress(current, done, total):
        if current == "anonymize" and done == 2:
            raise Cancelled

    with pytest.raises(Cancelled):
        anonymize(src, tmp_path / "out.pdf", TERMS, progress)


@pytest.mark.skipif(not ner.is_available(), reason="modelo NER no instalado")
def test_cancel_during_name_detection(tmp_path):
    src = _pdf(tmp_path / "doc.pdf", pages=40)

    def progress(current, done, total):
        if current == "detect" and done == 1:
            raise Cancelled

    with pytest.raises(Cancelled):
        analyze(src, [], CATALAN, progress)
