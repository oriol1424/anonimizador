"""Carpeta de salida en la que no se puede escribir (error del Mac del bufete, 2026-11-26).

Algunas pruebas solo tienen sentido en macOS/Linux: Windows no deja crear carpetas que
acaben en espacio y `chmod` no quita el permiso de escritura a una carpeta. En GitHub se
ejecutan en el Mac (flujo tests)."""

import os
import sys
from pathlib import Path

import pytest

from anonimizador.core import pdf_io
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import AnonymizerError, anonymize

TERMS = [Term("Joan Puig i Ferrer", "[CLIENT_1]")]
POSIX = pytest.mark.skipif(sys.platform == "win32", reason="solo macOS/Linux")


@pytest.fixture
def window(qtbot, tmp_path):
    from anonimizador.ui.main_window import MainWindow

    w = MainWindow(keep_path=tmp_path / "no_anonimitzar.json", log_path=tmp_path / "errors.log")
    qtbot.addWidget(w)
    return w


@POSIX
def test_folder_ending_in_space_saves_inside_it(window, demanda_ca: Path, tmp_path: Path):
    """En el Mac una carpeta puede llamarse «Clients ». Antes se validaba con el espacio y
    se guardaba sin él (carpeta inexistente → FileNotFoundError)."""
    folder = tmp_path / "Clients "
    folder.mkdir()
    window.folder_edit.setText(str(folder))
    window.name_edit.setText("sortida")
    out = window.output_path()
    assert out.parent == folder
    anonymize(demanda_ca, out, TERMS)
    assert (folder / out.name).exists()


def test_folder_with_spaces_typed_by_mistake_is_trimmed(window, tmp_path: Path):
    window.folder_edit.setText(f"  {tmp_path}  ")
    window.name_edit.setText("sortida")
    assert window.output_path().parent == tmp_path


@POSIX
@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root escribe igual")
def test_read_only_folder_fails_before_processing(demanda_pdf: Path, tmp_path: Path, monkeypatch):
    folder = tmp_path / "nomes_lectura"
    folder.mkdir()
    folder.chmod(0o555)
    started = []
    monkeypatch.setattr(pdf_io, "anonymize", lambda *a, **k: started.append(1))
    try:
        with pytest.raises(AnonymizerError) as error:
            anonymize(demanda_pdf, folder / "sortida.pdf", TERMS)
        assert error.value.kind == "cannot_write"
        assert error.value.params["reason"]  # «Permission denied»: se ve en pantalla
        assert not started
        assert list(folder.iterdir()) == []  # la prueba no deja ficheros
    finally:
        folder.chmod(0o755)


def test_writable_check_leaves_no_files(demanda_ca: Path, tmp_path: Path):
    out_dir = tmp_path / "sortida"
    out_dir.mkdir()
    anonymize(demanda_ca, out_dir / "sortida.docx", TERMS)
    assert [p.name for p in out_dir.iterdir()] == ["sortida.docx"]


def _fail_writes(monkeypatch, target: str, exc: OSError):
    """Hace fallar la escritura de un tipo de salida, con la comprobación previa en verde."""
    if target == "docx":
        from docx.document import Document

        def broken(self, *a, **k):
            raise exc

        monkeypatch.setattr(Document, "save", broken)
    elif target == "text":
        original = Path.write_text

        def broken_text(self, *a, **k):
            if self.suffix in (".md", ".txt"):
                raise exc
            return original(self, *a, **k)

        monkeypatch.setattr(Path, "write_text", broken_text)


@pytest.mark.parametrize(
    "exc",
    [FileNotFoundError(2, "No such file or directory"), PermissionError(13, "Permission denied")],
)
def test_word_save_error_gives_clear_message(demanda_ca: Path, tmp_path: Path, monkeypatch, exc):
    """El error exacto del Mac (2026-11-26): FileNotFoundError al guardar el Word."""
    _fail_writes(monkeypatch, "docx", exc)
    with pytest.raises(AnonymizerError) as error:
        anonymize(demanda_ca, tmp_path / "sortida.docx", TERMS)
    assert error.value.kind == "cannot_write"
    assert error.value.params["reason"] == exc.strerror
    assert not (tmp_path / "sortida.docx").exists()


@pytest.mark.parametrize("suffix", [".md", ".txt"])
def test_text_output_save_error_gives_clear_message(
    demanda_ca: Path, tmp_path: Path, monkeypatch, suffix
):
    _fail_writes(monkeypatch, "text", PermissionError(13, "Permission denied"))
    with pytest.raises(AnonymizerError) as error:
        anonymize(demanda_ca, tmp_path / f"sortida{suffix}", TERMS)
    assert error.value.kind == "cannot_write"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["demanda_ca.docx"]  # ni .tmp


def test_guide_save_error_gives_clear_message_and_no_output(
    demanda_pdf: Path, tmp_path: Path, monkeypatch
):
    """La guía falla (p. ej. la anterior está abierta en Word): mensaje claro y no queda
    el documento sin su guía."""
    from anonimizador.core import pipeline

    def broken(*a, **k):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(pipeline, "write_guide", broken)
    out = tmp_path / "sortida.pdf"
    with pytest.raises(AnonymizerError) as error:
        anonymize(demanda_pdf, out, TERMS, guide=tmp_path / "guia.docx")
    assert error.value.kind == "cannot_write"
    assert not out.exists()


def test_cleanup_failure_does_not_hide_the_real_error(
    demanda_ca: Path, tmp_path: Path, monkeypatch
):
    """Crítico: si borrar la salida a medias falla, antes salía ese error técnico."""
    _fail_writes(monkeypatch, "docx", PermissionError(13, "Permission denied"))

    def cannot_unlink(self, *a, **k):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "unlink", cannot_unlink)
    with pytest.raises(AnonymizerError) as error:
        anonymize(demanda_ca, tmp_path / "sortida.docx", TERMS)
    assert error.value.kind == "cannot_write"


def test_real_mupdf_message_gives_only_the_reason(demanda_pdf: Path, tmp_path: Path, monkeypatch):
    """Mensaje real de MuPDF: se queda solo el motivo, sin la ruta (puede llevar nombres)."""
    import pymupdf

    def refuse(self, filename, *a, **k):
        raise pymupdf.mupdf.FzErrorSystem(
            f"code=2: cannot remove file '{filename}': Permission denied"
        )

    monkeypatch.setattr(pymupdf.Document, "save", refuse)
    with pytest.raises(AnonymizerError) as error:
        anonymize(demanda_pdf, tmp_path / "Joan Puig.pdf", TERMS)
    assert error.value.params["reason"] == "Permission denied"


def test_log_records_cause_and_folder_kind_but_no_path(tmp_path: Path):
    from anonimizador.core import errlog

    try:
        try:
            raise FileNotFoundError(2, "No such file", "/Users/x/Desktop/Joan Puig/a.pdf")
        except OSError as exc:
            raise AnonymizerError(
                "cannot_write", folder="/Users/x/Desktop/Joan Puig ", reason="x"
            ) from exc
    except AnonymizerError as error:
        text = errlog.entry(error, "progress_anonymizing")
    assert "codi: cannot_write" in text
    assert "carpeta: Escriptori · el nom acaba en espai" in text
    assert "causa: builtins.FileNotFoundError ENOENT" in text
    assert "Joan" not in text and "Puig" not in text


def test_guide_with_any_invalid_xml_character(tmp_path: Path):
    from collections import Counter

    from anonimizador.core.guide import GuideEntry, write_guide
    from anonimizador.core.lang import CATALAN

    bad = "A\x00B\x0bC\x1fD\ud800E\ufffeF\uffffG"
    entry = GuideEntry("[PERSONA_1]", "PERSONA", [bad], Counter({bad: 1}))
    write_guide(tmp_path / "g.docx", [entry], Path("a.pdf"), Path("b.pdf"), CATALAN)
