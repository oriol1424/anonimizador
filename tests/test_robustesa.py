"""Robustez: una página que falla no aborta el proceso ni deja datos; el original nunca se
sobrescribe; un error no deja una salida a medias."""

import os
from pathlib import Path

import pymupdf
import pytest

from anonimizador.core import pdf_io
from anonimizador.core.lang import CATALAN, SPANISH
from anonimizador.core.matcher import Matcher, Term
from anonimizador.core.pipeline import AnonymizerError, analyze, anonymize

TERMS = [Term("Joan Puig i Ferrer", "[CLIENT_1]")]


def _two_pages(path: Path) -> Path:
    doc = pymupdf.open()
    for n in (1, 2):
        doc.new_page().insert_text((56, 72), f"Pagina {n}: en Joan Puig i Ferrer, DNI 12345678Z.")
    doc.save(str(path))
    return path


def _fail_on_page(monkeypatch, name: str, number: int) -> None:
    """Hace que `pdf_io.<name>` falle solo con la página `number` (desde 0)."""
    original = getattr(pdf_io, name)

    def broken(page, *args, **kwargs):
        if page.number == number:
            raise RuntimeError("pàgina danyada")
        return original(page, *args, **kwargs)

    monkeypatch.setattr(pdf_io, name, broken)


def _page_texts(path: Path) -> list[str]:
    with pymupdf.open(str(path)) as doc:
        return [page.get_text() for page in doc]


def test_failed_text_page_is_replaced_not_kept(tmp_path, monkeypatch):
    src = _two_pages(tmp_path / "doc.pdf")
    _fail_on_page(monkeypatch, "_anonymize_text_page", 0)
    out = tmp_path / "sortida.pdf"
    report = anonymize(src, out, TERMS)
    first, second = _page_texts(out)
    assert first.strip() == "[Pàgina 1 no processada]"
    assert "Joan" not in second and "[CLIENT_1]" in second
    failed = [n for n in report.notices if n.kind == "failed_pages"]
    assert failed and failed[0].pages == "1" and failed[0].is_serious


def test_failed_page_text_follows_language(tmp_path, monkeypatch):
    src = _two_pages(tmp_path / "doc.pdf")
    _fail_on_page(monkeypatch, "_anonymize_text_page", 1)
    out = tmp_path / "sortida.pdf"
    anonymize(src, out, TERMS, language=SPANISH)
    assert _page_texts(out)[1].strip() == "[Página 2 no procesada]"


@pytest.mark.parametrize("step", ["_start_image_page", "_finish_image_page"])
def test_failed_scanned_page_is_replaced(demanda_pdf, tmp_path, monkeypatch, step):
    """La página 2 del PDF de prueba es escaneada: falla al borrar o al verificar."""
    if step == "_finish_image_page":

        def broken(page, state, matcher):
            raise RuntimeError("OCR fallat")

        monkeypatch.setattr(pdf_io, "_finish_image_page", broken)
    else:
        _fail_on_page(monkeypatch, step, 1)
    out = tmp_path / "sortida.pdf"
    report = anonymize(demanda_pdf, out, TERMS)
    with pymupdf.open(str(out)) as doc:
        assert doc.page_count == 2
        assert doc[1].get_text().strip() == "[Pàgina 2 no processada]"
        assert not doc[1].get_images()  # ni rastro de la imagen escaneada
        assert "Joan" not in doc[0].get_text()
    assert [n.pages for n in report.notices if n.kind == "failed_pages"] == ["2"]


def test_unreadable_page_in_analysis_is_skipped_and_reported(tmp_path, monkeypatch):
    src = _two_pages(tmp_path / "doc.pdf")
    _fail_on_page(monkeypatch, "_page_text", 0)
    analysis = analyze(src, [], CATALAN)
    assert any("12345678Z" in s.forms for s in analysis.suggestions)  # de la página 2
    notice = [n for n in analysis.notices if n.kind == "unreadable_pages"]
    assert notice and notice[0].pages == "1" and notice[0].is_serious


def test_failed_page_in_text_export(tmp_path, monkeypatch):
    src = _two_pages(tmp_path / "doc.pdf")
    _fail_on_page(monkeypatch, "_page_text", 0)
    failed: set[int] = set()
    text = pdf_io.anonymized_text(src, Matcher(TERMS), failed=failed)
    assert text.startswith("[Pàgina 1 no processada]")
    assert "Joan" not in text and "[CLIENT_1]" in text
    assert failed == {1}


def test_error_leaves_no_partial_output(tmp_path, monkeypatch):
    src = _two_pages(tmp_path / "doc.pdf")

    def broken(*args, **kwargs):
        raise RuntimeError("disc ple")

    monkeypatch.setattr(pdf_io, "extract_text", broken)  # falla la verificación final
    out = tmp_path / "sortida.pdf"
    with pytest.raises(RuntimeError):
        anonymize(src, out, TERMS)
    assert not out.exists()
    assert src.exists()


def _case_insensitive(folder: Path) -> bool:
    probe = folder / "Prova.txt"
    probe.write_text("x")
    return (folder / "prova.txt").exists()


def test_output_with_other_case_is_the_same_file(demanda_ca, tmp_path):
    if not _case_insensitive(tmp_path):
        pytest.skip("sistema de ficheros sensible a mayúsculas")
    upper = demanda_ca.with_name(demanda_ca.name.upper().replace(".DOCX", ".docx"))
    before = demanda_ca.read_bytes()
    with pytest.raises(AnonymizerError) as error:
        anonymize(demanda_ca, upper, TERMS)
    assert error.value.kind == "same_file"
    assert demanda_ca.read_bytes() == before


def test_guide_cannot_overwrite_the_original(demanda_ca, tmp_path):
    before = demanda_ca.read_bytes()
    with pytest.raises(AnonymizerError):
        anonymize(demanda_ca, tmp_path / "sortida.docx", TERMS, guide=demanda_ca)
    assert demanda_ca.read_bytes() == before


def test_same_file_through_other_path(demanda_ca):
    other = Path(os.path.relpath(demanda_ca))  # misma ruta, escrita de otra manera
    with pytest.raises(AnonymizerError):
        anonymize(demanda_ca, other, TERMS)
