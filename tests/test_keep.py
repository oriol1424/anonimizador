"""Nombres y datos que no se anonimizan nunca (p. ej. la abogada del despacho)."""

import zipfile
from pathlib import Path

from anonimizador.core import keep_list
from anonimizador.core.lang import CATALAN
from anonimizador.core.matcher import Matcher, Term, keep_term
from anonimizador.core.pipeline import analyze, anonymize

LAWYER = "Montserrat Soler i Vidal"


def test_kept_name_is_found_but_not_replaced():
    m = Matcher([keep_term(LAWYER)])
    text = "La lletrada Montserrat Soler i Vidal signa."
    assert m.find(text) == []
    assert m.replace(text) == text
    assert [x.text for x in m.find(text, include_kept=True)] == [LAWYER]


def test_kept_name_protects_its_surname_from_other_terms():
    m = Matcher([Term("Pere Soler", "[CLIENT_1]"), keep_term(LAWYER)])
    text = "Montserrat Soler i Vidal defensa en Pere Soler. El Sr. Soler hi està d'acord."
    assert m.replace(text) == (
        "Montserrat Soler i Vidal defensa en [CLIENT_1]. El Sr. [CLIENT_1] hi està d'acord."
    )


def test_kept_multiword_variants_are_protected_but_not_a_lone_surname():
    m = Matcher([Term("Pere Soler", "[CLIENT_1]"), keep_term(LAWYER)])
    assert m.replace("Montserrat Soler ho confirma") == "Montserrat Soler ho confirma"
    assert m.replace("Montserrat Soler Vidal ho confirma") == "Montserrat Soler Vidal ho confirma"
    # Un apellido suelto podría ser del cliente: se sigue anonimizando.
    assert m.replace("Soler ho confirma") == "[CLIENT_1] ho confirma"


def test_user_list_wins_over_keep_list():
    m = Matcher([keep_term("Anna Vila"), Term("Anna Vila", "[PERSONA_1]")])
    assert m.replace("Anna Vila") == "[PERSONA_1]"


def test_kept_items_are_not_suggested(demanda_ca: Path):
    keep = [keep_term(LAWYER), keep_term("info@soler-associats.example"),
            keep_term("972 123 456")]  # fmt: skip
    forms = {f for s in analyze(demanda_ca, keep, CATALAN).suggestions for f in s.forms}
    assert "info@soler-associats.example" not in forms
    assert "972 123 456" not in forms
    assert not [f for f in forms if f.startswith("Montserrat")]


def test_kept_items_survive_anonymization(demanda_ca: Path, tmp_path: Path):
    terms = [Term("Joan Puig i Ferrer", "[CLIENT_1]"), keep_term(LAWYER)]
    analysis = analyze(demanda_ca, terms, CATALAN)
    for s in analysis.suggestions:
        terms.extend(s.to_terms())
    out = tmp_path / "sortida.docx"
    guide = tmp_path / "guia.docx"
    report = anonymize(demanda_ca, out, terms, guide=guide)
    with zipfile.ZipFile(out) as z:
        header = z.read("word/header1.xml").decode("utf-8")
        everything = "".join(
            z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.endswith(".xml")
        )
    assert LAWYER in header  # la abogada sigue en la cabecera
    assert "Joan" not in everything
    assert not [n for n in report.notices if n.is_leak]  # no es un «dato que queda»
    assert not [e for e in report.entries if LAWYER in e.originals]  # ni sale en la guía
    assert LAWYER not in report.replaced


def test_keep_list_is_saved_and_loaded(tmp_path: Path):
    path = tmp_path / "config" / "no_anonimitzar.json"
    assert keep_list.load(path) == []
    keep_list.save(path, [LAWYER, " ", LAWYER, "Despatx Soler & Associats"])
    assert keep_list.load(path) == [LAWYER, "Despatx Soler & Associats"]


def test_damaged_keep_list_is_ignored(tmp_path: Path):
    path = tmp_path / "no_anonimitzar.json"
    path.write_text("{no és json", encoding="utf-8")
    assert keep_list.load(path) == []
