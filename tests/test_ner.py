"""Detector de personas y empresas (modelo AINA en ONNX) + direcciones por reglas.

Si el modelo no está instalado (`models/ner-ca/`, ver scripts/preparar_models.py) estos
tests se saltan; el resto de la app funciona sin él.
"""

from pathlib import Path

import pytest
from ner_eval_ca import EXAMPLES

from anonimizador.core import ner, regex_es
from anonimizador.core.lang import CATALAN
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import analyze, anonymize

needs_model = pytest.mark.skipif(not ner.is_available(), reason="modelo NER no instalado")


def _covered(text: str, start: int, end: int, spans) -> float:
    chars = set()
    for s, e in spans:
        chars |= set(range(max(start, s), min(end, e)))
    return len(chars) / (end - start)


@needs_model
def test_evaluation_set_recall_and_precision():
    found = total = false_positives = 0
    for text, gold in EXAMPLES:
        spans = [(e.start, e.end) for e in ner.detect(text)]
        spans += [(d.start, d.end) for d in regex_es.detect(text) if d.label == "DIRECCION"]
        gold_spans = [(text.index(f), text.index(f) + len(f)) for f, _ in gold]
        for gs, ge in gold_spans:
            total += 1
            found += _covered(text, gs, ge, spans) >= 0.8
        false_positives += sum(
            1 for s, e in spans if not any(s < ge and e > gs for gs, ge in gold_spans)
        )
    assert found / total >= 0.95, f"{found}/{total}"
    assert false_positives <= 2


@needs_model
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("La Sra. Remei Tarrés i Canals reclama a TRANSPORTS ALT EMPORDÀ SCCL.",
         {"Remei Tarrés i Canals", "TRANSPORTS ALT EMPORDÀ SCCL"}),
        ("ELS FETS: el demandat, ORIOL PLANAS MIRÓ, no va pagar.", {"ORIOL PLANAS MIRÓ"}),
        ("La part contrària, Martí d’Orriols, no ha pagat.", {"Martí d’Orriols"}),
        ("La testigo, Doña Carmen López Ortega, vio a Javier Moreno.",
         {"Carmen López Ortega", "Javier Moreno"}),
    ],
)  # fmt: skip
def test_detects_people_and_companies(text, expected):
    assert expected <= {e.text for e in ner.detect(text)}


@needs_model
@pytest.mark.parametrize(
    "text",
    [
        "El Jutjat de Primera Instància núm. 3 de Girona i l'Agència Tributària.",
        "El Juzgado de Primera Instancia n.º 5 y el Ayuntamiento de Madrid.",
        "Demandat",
        "El Sr. i la Sra. van comparèixer.",
    ],
)
def test_ignores_public_bodies_roles_and_titles(text):
    assert ner.detect(text) == []


@needs_model
def test_suggestions_in_catalan_document(demanda_ca: Path):
    terms = [Term("Joan Puig i Ferrer", "[CLIENT_1]")]
    suggestions = analyze(demanda_ca, terms, CATALAN).suggestions
    by_text = {s.text: s for s in suggestions}
    for name in ["Marcel·lí Roca", "Anna Vila", "Montserrat Soler i Vidal"]:
        assert by_text[name].label == "PERSONA" and by_text[name].expand
    orriols = by_text["Martí d’Orriols"]
    assert orriols.count == 2  # "Martí d’Orriols" + "L’Orriols", unidas
    assert by_text["Carrer Major 5, Girona"].replacement == "[ADRECA_1]"
    assert suggestions[0].label == "PERSONA"  # primero lo más identificativo
    assert not [s for s in suggestions if s.text in {"Joan", "Demandat", "Puig"}]


@needs_model
def test_accepting_all_suggestions_leaves_no_names(demanda_ca: Path, tmp_path: Path):
    terms = [Term("Joan Puig i Ferrer", "[CLIENT_1]")]
    for s in analyze(demanda_ca, terms, CATALAN).suggestions:
        terms.extend(s.to_terms())
    out = tmp_path / "sortida.txt"
    anonymize(demanda_ca, out, terms)
    text = out.read_text(encoding="utf-8")
    for secret in ["Orriols", "Marcel", "Roca", "Anna Vila", "Montserrat", "VALLÈS", "Major 5"]:
        assert secret not in text


def test_without_model_the_app_still_works(demanda_ca: Path, monkeypatch):
    monkeypatch.setattr(ner, "is_available", lambda: False)
    analysis = analyze(demanda_ca, [], CATALAN)
    assert any(n.kind == "ner_unavailable" for n in analysis.notices)
    assert any(s.label == "DNI" for s in analysis.suggestions)


@needs_model
def test_repeated_chunks_are_found_everywhere(monkeypatch):
    """Los trozos repetidos (cabeceras, pies) se analizan una vez pero se marcan todos."""
    monkeypatch.setattr(ner, "CHUNK_CHARS", 60)
    header = "Despatx Casals · Lletrat Jordi Casals i Pons\n"
    body = "La senyora Laura Fontanals Pujol va signar el contracte.\n"
    text = (header + body) * 3
    found = [(e.start, e.text) for e in ner.detect(text)]
    for k in range(3):
        offset = k * len(header + body)
        assert (offset + header.index("Jordi"), "Jordi Casals i Pons") in found
        assert (offset + len(header) + body.index("Laura"), "Laura Fontanals Pujol") in found


@needs_model
def test_detector_self_check_passes():
    ner._working = None
    assert ner.is_working()


def test_broken_detector_is_reported(demanda_ca: Path, monkeypatch):
    """Si el modelo no reconoce ni un nombre evidente (procesador incompatible), se avisa
    en rojo en vez de seguir como si el documento no tuviera nombres."""
    monkeypatch.setattr(ner, "is_available", lambda: True)
    monkeypatch.setattr(ner, "_working", False)
    monkeypatch.setattr(ner, "detect", lambda *a, **k: [])
    notices = analyze(demanda_ca, [], CATALAN).notices
    broken = [n for n in notices if n.kind == "ner_broken"]
    assert broken and broken[0].is_serious
