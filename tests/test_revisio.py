"""Revisión final, registro de errores sin datos y «Quant a»."""

from pathlib import Path

from anonimizador.core import errlog
from anonimizador.core.review import suspicious

TEXT = (
    "AL JUTJAT DE LA BATLLIA\n"
    "En [CLIENT_1], major d'edat, compareix. El testimoni Jordi Casals ho confirma davant "
    "la Batllia d'Andorra.\nPrimer. Que el Sr. Casals va signar l'Article 5 de la Llei "
    "qualificada el 3 de Març de 2024. Segons Roca, el deute és ferm.\nSUPLICO: Que es tingui."
)


def test_suspicious_words():
    assert suspicious(TEXT) == [("Casals", 2), ("Jordi", 1), ("Roca", 1)]


def test_keep_list_is_not_flagged():
    assert suspicious(TEXT, {"Jordi Casals i Pons"}) == [("Roca", 1)]


def test_aliases_and_sentence_starts_are_ignored():
    assert suspicious("[PERSONA_1] signa. Després [EMPRESA_1] paga.") == []


def test_error_log_has_no_document_text(tmp_path: Path):
    try:
        {}["Joan Puig i Ferrer, DNI 12345678Z"]
    except KeyError as error:
        path = errlog.write(tmp_path / "logs" / "errors.log", error, "progress_analyzing")
    text = path.read_text(encoding="utf-8")
    assert "KeyError" in text and "progress_analyzing" in text and "test_revisio.py" in text
    assert "Joan" not in text and "12345678Z" not in text


def test_error_log_is_trimmed(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(errlog, "MAX_BYTES", 2_000)
    path = tmp_path / "errors.log"
    for _ in range(50):
        errlog.write(path, ValueError(), "x")
    assert path.stat().st_size < 4_000
    assert path.read_text(encoding="utf-8").startswith("=== ")


def test_about_dialog(qtbot):
    from PySide6.QtWidgets import QLabel

    from anonimizador import __version__
    from anonimizador.ui.about_dialog import AboutDialog

    dialog = AboutDialog("ca")
    qtbot.addWidget(dialog)
    texts = " ".join(w.text() for w in dialog.findChildren(QLabel))
    assert __version__ in texts and "AGPL" in texts and "codi_font" in texts
