"""Casos en catalán: el idioma de la práctica totalidad de los documentos del bufete."""

import zipfile
from pathlib import Path

import pytest
from docx import Document

from anonimizador.core import docx_io
from anonimizador.core.lang import CATALAN, SPANISH
from anonimizador.core.matcher import Matcher, Term, variants
from anonimizador.core.pipeline import analyze, anonymize

USER_TERMS = [
    Term("Joan Puig i Ferrer", "[CLIENT_1]"),
    Term("Construccions del Vallès SL", "[EMPRESA_1]"),
    Term("Montserrat Soler i Vidal", "[ADVOCAT_1]"),
    Term("Martí d'Orriols", "[PART_CONTRARIA_1]"),
    Term("Marcel·lí Roca", "[PERSONA_1]"),
    Term("Anna Vila", "[PERSONA_2]"),
]


# --- Matcher -------------------------------------------------------------------------


def test_variants_with_conjunction_i():
    v = set(variants("Joan Puig i Ferrer"))
    assert {"Joan Puig", "Puig i Ferrer", "J. Puig i Ferrer", "Puig", "Ferrer"} <= v
    assert "i" not in v and "i Ferrer" not in v


def test_conjunction_is_optional():
    m = Matcher([Term("Joan Puig i Ferrer", "[CLIENT_1]")])
    assert m.replace("Joan Puig Ferrer i Joan Puig i Ferrer") == "[CLIENT_1] i [CLIENT_1]"
    m = Matcher([Term("Joan Puig Ferrer", "[CLIENT_1]")])
    assert m.replace("En Joan Puig i Ferrer compareix") == "En [CLIENT_1] compareix"


@pytest.mark.parametrize("apostrophe", ["'", "’"])
def test_elision_with_any_apostrophe(apostrophe):
    m = Matcher([Term("Martí d'Orriols", "[PART_CONTRARIA_1]")])
    text = f"El Sr. Martí d{apostrophe}Orriols i l{apostrophe}Orriols. D{apostrophe}Orriols va dir."
    assert m.replace(text) == (
        f"El Sr. [PART_CONTRARIA_1] i l{apostrophe}[PART_CONTRARIA_1]. [PART_CONTRARIA_1] va dir."
    )


def test_middle_dot_is_part_of_the_word():
    m = Matcher([Term("Marcel·lí Roca", "[PERSONA_1]")])
    assert m.replace("El perit Marcel·lí Roca; el senyor Roca.") == (
        "El perit [PERSONA_1]; el senyor [PERSONA_1]."
    )
    m = Matcher([Term("Marcel", "[X]")])
    assert m.replace("Marcel·lí no és Marcel") == "Marcel·lí no és [X]"


def test_common_catalan_words_untouched():
    m = Matcher([Term("Carrer Major 5", "[ADRECA_1]")])
    assert m.replace("Viu al Carrer Major 5 i és major d'edat.") == (
        "Viu al [ADRECA_1] i és major d'edat."
    )


def test_shared_surname_in_catalan():
    m = Matcher([Term("Joan Puig", "[PERSONA_1]"), Term("Pere Puig", "[PERSONA_2]")])
    assert m.replace("El senyor Puig.") == "El senyor Puig."
    assert "Puig" in m.ambiguous


# --- Documento completo --------------------------------------------------------------


def _raw_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith((".xml", ".rels"))]
        return "\n".join(z.read(n).decode("utf-8", "ignore") for n in names)


@pytest.fixture
def anonymized_ca(demanda_ca: Path, tmp_path: Path):
    terms = list(USER_TERMS)
    analysis = analyze(demanda_ca, terms, CATALAN)
    for s in analysis.suggestions:
        terms.extend(s.to_terms())
    out = tmp_path / "sortida.docx"
    return out, anonymize(demanda_ca, out, terms), analysis


@pytest.mark.parametrize(
    "secret",
    [
        "Joan", "Puig", "Ferrer", "Vallès", "VALLÈS", "Montserrat", "Soler", "Vidal",
        "Orriols", "Marcel", "Roca", "Anna Vila", "12345678Z", "B12345674", "2100 0418",
        "972 123 456", "joan.puig", "soler-associats", "1234 BCD", "1234/2025",
    ],
)  # fmt: skip
def test_nothing_sensitive_left_in_catalan_doc(anonymized_ca, secret):
    out, _, _ = anonymized_ca
    assert secret not in _raw_xml(out)


def test_catalan_text_and_format_preserved(anonymized_ca):
    out, report, _ = anonymized_ca
    text = docx_io.body_text(out)
    assert "En [CLIENT_1], major d’edat" in text
    assert "L’[PART_CONTRARIA_1] no ha pagat" in text
    assert "viu al carrer major del poble" in text
    p = Document(str(out)).paragraphs[1]
    assert "[CLIENT_1]" in "".join(r.text for r in p.runs if r.bold)
    assert not [w for w in report.warnings if w.startswith("Verificación")]


def test_suggestion_aliases_in_catalan(anonymized_ca):
    _, _, analysis = anonymized_ca
    aliases = {s.replacement for s in analysis.suggestions}
    assert {"[TELEFON_1]", "[CORREU_1]", "[PROCEDIMENT_1]", "[NIF_EMPRESA_1]"} <= aliases


def test_suggestion_aliases_in_spanish(demanda: Path):
    aliases = {s.replacement for s in analyze(demanda, [], SPANISH).suggestions}
    assert {"[TELEFONO_1]", "[EMAIL_1]", "[PROCEDIMIENTO_1]", "[CIF_1]"} <= aliases


def test_default_language_is_catalan(demanda_ca: Path):
    aliases = {s.replacement for s in analyze(demanda_ca, []).suggestions}
    assert "[TELEFON_1]" in aliases
