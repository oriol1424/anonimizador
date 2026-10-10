"""Pruebas de la ventana (sin pantalla: QT_QPA_PLATFORM=offscreen en conftest)."""

import json
import threading
from pathlib import Path

import pytest
from docx import Document
from PySide6.QtCore import QSettings, Qt

from anonimizador.core.lang import fill_preset
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import Analysis, Report
from anonimizador.ui.main_window import MainWindow
from anonimizador.ui.suggestions import SuggestionsDialog
from anonimizador.ui.worker import run_in_background


@pytest.fixture
def window(qtbot, tmp_path):
    w = MainWindow(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    qtbot.addWidget(w)
    return w


def test_fill_preset():
    assert fill_preset("[CLIENT_{n}]", set()) == "[CLIENT_1]"
    assert fill_preset("[CLIENT_{n}]", {"[CLIENT_1]", "[CLIENT_2]"}) == "[CLIENT_3]"
    assert fill_preset("***", {"***"}) == "***"


def test_starts_in_catalan(window):
    assert window.windowTitle() == "Anonimitzador"
    assert window.run_button.text() == "Anonimitza"
    assert window.language.code == "ca"
    assert window.table.combo(0).value() == "[PERSONA_1]"


def test_switch_to_spanish(window):
    window.language_combo.setCurrentIndex(window.language_combo.findData("es"))
    assert window.windowTitle() == "Anonimizador"
    assert window.run_button.text() == "Anonimizar"
    assert window.table.combo(0).itemText(1) == "[CLIENTE_n]"
    assert window.table.combo(0).value() == "[PERSONA_1]"  # no se pierde lo escrito


def test_presets_get_next_free_number(window):
    window.table.add_row()
    first, second = window.table.combo(0), window.table.combo(1)
    first.choose("[CLIENT_{n}]")
    second.choose("[CLIENT_{n}]")
    assert (first.value(), second.value()) == ("[CLIENT_1]", "[CLIENT_2]")


def test_input_sets_default_output(window, demanda_ca: Path):
    window.set_input(demanda_ca)
    assert window.folder_edit.text() == str(demanda_ca.parent)
    assert window.name_edit.text() == "demanda_ca_anonimitzat"
    window.format_combo.setCurrentIndex(1)
    assert window.output_path() == demanda_ca.parent / "demanda_ca_anonimitzat.txt"


def test_save_and_load_list(window, tmp_path):
    window.table.item(0, 0).setText("Joan Puig i Ferrer")
    window.table.combo(0).setEditText("[CLIENT_1]")
    path = tmp_path / "cas.json"
    data = {"idioma": "ca", "termes": [{"original": o, "substitut": r}
                                       for o, r in window.table.entries()]}  # fmt: skip
    path.write_text(json.dumps(data), encoding="utf-8")
    window.table.clear_rows()
    window.load_list_file(path)
    assert window.table.entries() == [("Joan Puig i Ferrer", "[CLIENT_1]")]


def test_background_callback_runs_in_ui_thread(qtbot):
    seen = {}
    main = threading.get_ident()

    def finished(value):
        seen["value"], seen["thread"] = value, threading.get_ident()

    run_in_background(lambda: threading.get_ident(), finished, lambda e: None)
    qtbot.waitUntil(lambda: "value" in seen, timeout=5000)
    assert seen["value"] != main  # la tarea corrió en otro hilo
    assert seen["thread"] == main  # el resultado llegó al hilo de la interfaz


def test_suggestions_dialog_returns_checked_terms(qtbot, demanda_ca: Path):
    from anonimizador.core.lang import CATALAN
    from anonimizador.core.pipeline import analyze

    analysis = analyze(demanda_ca, [], CATALAN)
    dialog = SuggestionsDialog(analysis, CATALAN, set())
    qtbot.addWidget(dialog)
    dni_row = next(i for i, s in enumerate(analysis.suggestions) if s.label == "DNI")
    dialog.combos[dni_row].setEditText("[DNI_CLIENT]")
    phone_row = next(i for i, s in enumerate(analysis.suggestions) if s.label == "TELEFONO")
    dialog.table.item(phone_row, 0).setCheckState(Qt.CheckState.Unchecked)

    terms = dialog.selected_terms()
    assert Term("12345678Z", "[DNI_CLIENT]", expand=False, source="DNI") in terms
    assert not [t for t in terms if t.source == "TELEFONO"]


def test_full_flow_from_window(window, qtbot, demanda_ca: Path, monkeypatch):
    window.set_input(demanda_ca)
    window.table.item(0, 0).setText("Joan Puig i Ferrer")
    window.table.combo(0).setEditText("[CLIENT_1]")

    def accept_all(analysis: Analysis, terms):
        return [t for s in analysis.suggestions for t in s.to_terms()]

    results: list[Report] = []
    monkeypatch.setattr(window, "ask_suggestions", accept_all)
    monkeypatch.setattr(window, "show_result", results.append)
    window.start()
    qtbot.waitUntil(lambda: bool(results), timeout=10000)

    out = demanda_ca.parent / "demanda_ca_anonimitzat.docx"
    assert results[0].output == out
    text = "\n".join(p.text for p in Document(str(out)).paragraphs)
    assert "Puig" not in text and "12345678Z" not in text
    assert "[CLIENT_1]" in text and "[DNI_1]" in text
    assert window.centralWidget().isEnabled()
