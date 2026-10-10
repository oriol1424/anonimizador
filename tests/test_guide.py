"""Guía de correspondencias y unión de variantes de un mismo nombre."""

from pathlib import Path

from docx import Document

from anonimizador.core import docx_io
from anonimizador.core.guide import default_path
from anonimizador.core.lang import CATALAN
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import Suggestion, anonymize, merge_variants

TERMS = [
    Term("Joan Puig i Ferrer", "[CLIENT_1]"),
    Term("Construccions del Vallès SL", "[EMPRESA_1]"),
    Term("Pere Inexistent", "[PERSONA_9]"),
    Term("12345678Z", "[DNI_1]", expand=False, source="DNI"),
]


def _rows(path: Path) -> dict[str, list[str]]:
    table = Document(str(path)).tables[0]
    return {row.cells[0].text: [c.text for c in row.cells] for row in table.rows[1:]}


def test_guide_lists_every_alias_with_its_original(demanda_ca: Path, tmp_path: Path):
    out = tmp_path / "sortida.docx"
    guide = default_path(out, CATALAN)
    report = anonymize(demanda_ca, out, TERMS, guide=guide, language=CATALAN)

    assert report.guide == guide == tmp_path / "sortida_GUIA_CONFIDENCIAL.docx"
    rows = _rows(guide)
    client = rows["[CLIENT_1]"]
    assert client[1] == "Joan Puig i Ferrer"
    assert "Puig" in client[2]  # "Sr. Puig" -> forma "Puig" encontrada
    assert int(client[4]) == report.replaced["[CLIENT_1]"]
    assert rows["[DNI_1]"][3] == "DNI"
    assert "No trobat" in rows["[PERSONA_9]"][2]  # avisa de términos mal escritos


def test_guide_has_confidential_warning_and_is_separate(demanda_ca: Path, tmp_path: Path):
    out = tmp_path / "sortida.docx"
    guide = default_path(out, CATALAN)
    anonymize(demanda_ca, out, TERMS, guide=guide, language=CATALAN)
    text = docx_io.body_text(guide)
    assert "CONFIDENCIAL" in text and "Joan Puig i Ferrer" in text
    assert "Joan Puig" not in docx_io.body_text(out)


def test_no_guide_unless_requested(demanda_ca: Path, tmp_path: Path):
    report = anonymize(demanda_ca, tmp_path / "sortida.docx", TERMS)
    assert report.guide is None
    assert not list(tmp_path.glob("*GUIA*"))
    assert {e.replacement for e in report.entries} >= {"[CLIENT_1]", "[DNI_1]"}


def test_merge_variants_of_same_person():
    suggestions = [
        Suggestion("PERSONA", "[PERSONA_1]", ("Jordi Casals i Pons",), 2, expand=True),
        Suggestion("PERSONA", "[PERSONA_2]", ("Casals",), 3, expand=True),
        Suggestion("PERSONA", "[PERSONA_3]", ("J. Casals Pons",), 1, expand=True),
        Suggestion("PERSONA", "[PERSONA_4]", ("Laia Mas",), 1, expand=True),
        Suggestion("DNI", "[DNI_1]", ("12345678Z",), 1),
    ]
    merged = merge_variants(suggestions)
    people = [s for s in merged if s.label == "PERSONA"]
    assert len(people) == 2
    jordi = next(s for s in people if s.text == "Jordi Casals i Pons")
    assert set(jordi.forms) == {"Jordi Casals i Pons", "Casals", "J. Casals Pons"}
    assert jordi.count == 6 and jordi.replacement == "[PERSONA_1]"
    assert any(s.label == "DNI" for s in merged)


def test_merge_does_not_mix_different_people():
    suggestions = [
        Suggestion("PERSONA", "[PERSONA_1]", ("Joan Puig",), 1, expand=True),
        Suggestion("PERSONA", "[PERSONA_2]", ("Pere Puig",), 1, expand=True),
    ]
    assert len(merge_variants(suggestions)) == 2
