import zipfile
from pathlib import Path

import pytest
from docx import Document

from anonimizador.core import docx_io
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import AnonymizerError, analyze, anonymize

USER_TERMS = [
    Term("Juan Pérez García", "[CLIENTE_1]"),
    Term("Construcciones Levante SL", "[EMPRESA_1]"),
    Term("Laura Martín Ruiz", "[ABOGADA_1]"),
    Term("Ana López", "[PERSONA_1]"),
]


def _raw_xml(path: Path) -> str:
    """Todo el XML del paquete: si un dato sobrevive en cualquier rincón, aparece aquí."""
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith((".xml", ".rels"))]
        return "\n".join(z.read(n).decode("utf-8", "ignore") for n in names)


@pytest.fixture
def anonymized(demanda: Path, tmp_path: Path):
    terms = list(USER_TERMS)
    for s in analyze(demanda, terms).suggestions:
        terms.extend(s.to_terms())
    out = tmp_path / "salida.docx"
    return out, anonymize(demanda, out, terms)


@pytest.mark.parametrize(
    "secret",
    [
        "Juan",
        "Pérez",
        "García",
        "Levante",
        "Laura",
        "Martín",
        "Ana López",
        "12345678Z",
        "B12345674",
        "2100 0418",
        "612 345 678",
        "juan.perez",
        "1234 BCD",
        "1234/2025",
    ],
)
def test_nothing_sensitive_left_anywhere(anonymized, secret):
    out, _ = anonymized
    assert secret not in _raw_xml(out)


def test_formatting_is_preserved(anonymized):
    out, _ = anonymized
    p = Document(str(out)).paragraphs[1]
    assert p.text.startswith("Don [CLIENTE_1], mayor de edad")
    bold_runs = [r.text for r in p.runs if r.bold]
    assert "[CLIENTE_1]" in "".join(bold_runs)


def test_common_words_untouched(anonymized):
    out, _ = anonymized
    text = docx_io.body_text(out)
    assert "mayor de edad y vive en la calle mayor del pueblo" in text


def test_report_and_no_leftovers(anonymized):
    _, report = anonymized
    assert report.replaced["[CLIENTE_1]"] >= 5
    assert not [n for n in report.notices if n.kind == "leftovers"]


def test_suggestions_find_unlisted_data(demanda: Path):
    labels = {s.label for s in analyze(demanda, USER_TERMS).suggestions}
    assert {"DNI", "CIF", "IBAN", "TELEFONO", "EMAIL", "MATRICULA", "PROCEDIMIENTO"} <= labels


def test_txt_output(demanda: Path, tmp_path: Path):
    out = tmp_path / "salida.txt"
    anonymize(demanda, out, USER_TERMS)
    text = out.read_text(encoding="utf-8")
    assert "[CLIENTE_1]" in text and "Pérez" not in text
    assert not list(tmp_path.glob("*.tmp.docx"))


def test_refuses_to_overwrite_original(demanda: Path):
    with pytest.raises(AnonymizerError):
        anonymize(demanda, demanda, USER_TERMS)
