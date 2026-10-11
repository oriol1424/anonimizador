"""Demanda andorrana inventada, de principio a fin (Word y PDF): el caso habitual del bufete.

Pasaporte, NRT, CASS, permiso de residencia, teléfonos +376, AD500... deben desaparecer;
los organismos (Batllia, Comú, CASS como institución, BOPA) deben quedarse.
"""

import zipfile
from dataclasses import dataclass
from pathlib import Path

import pymupdf
import pytest
from generar_corpus import build_demanda_andorra, build_demanda_andorra_pdf

from anonimizador.core import docx_io, ner, pdf_io
from anonimizador.core.lang import CATALAN
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import analyze, anonymize

# Lo que pondría el abogado en su lista; el resto debe salir de las sugerencias.
USER_TERMS = [
    Term("Pere Riba i Montané", "[CLIENT_1]"),
    Term("Laura Fontanals Pujol", "[PART_CONTRARIA_1]"),
    Term("Esquís Pirineu SL", "[EMPRESA_1]"),
    Term("Jordi Casals i Pons", "[ADVOCAT_1]"),
    Term("Núria Serra", "[PERSONA_1]"),
]

SECRETS = [
    "Pere", "Riba", "Montané", "Laura", "Fontanals", "Pujol", "Esquís", "ESQUÍS", "Casals",
    "Núria Serra", "O1234567", "CB1234567", "L-712345-B", "F-654321-Z", "123456",
    "12345/2020", "812 345", "361 234", "712 345", "Meritxell", "AD500",
    "AD12 0001 2030", "A 1234", "1234/2025", "pere.riba", "casals-advocats",
]  # fmt: skip

KEPT = [
    "BATLLIA D'ANDORRA", "Caixa Andorrana de Seguretat Social", "la CASS no",
    "Butlletí Oficial del Principat d'Andorra", "Comú d'Andorra la Vella", "Cos de Policia",
]  # fmt: skip

BUILDERS = {".docx": build_demanda_andorra, ".pdf": build_demanda_andorra_pdf}


def _everything(path: Path) -> str:
    """Todo lo legible del fichero: XML completo del Word; texto, metadatos y caracteres
    del PDF."""
    if path.suffix == ".docx":
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.endswith((".xml", ".rels"))]
            return "\n".join(z.read(n).decode("utf-8", "ignore") for n in names)
    doc = pymupdf.open(str(path))
    parts = [pdf_io.extract_text(path), str(doc.metadata), doc.get_xml_metadata()]
    parts += [repr(page.get_text("rawdict")) for page in doc]
    doc.close()
    return "\n".join(parts)


def _visible_text(path: Path) -> str:
    return docx_io.body_text(path) if path.suffix == ".docx" else pdf_io.extract_text(path)


@dataclass
class Run:
    src: Path
    out: Path
    report: object
    analysis: object


@pytest.fixture(scope="module", params=[".docx", ".pdf"])
def run(request, tmp_path_factory) -> Run:
    folder = tmp_path_factory.mktemp("andorra")
    src = BUILDERS[request.param](folder / f"demanda_andorra{request.param}")
    terms = list(USER_TERMS)
    analysis = analyze(src, terms, CATALAN)
    for s in analysis.suggestions:  # el usuario acepta todas las sugerencias
        terms.extend(s.to_terms())
    out = folder / f"sortida{request.param}"
    return Run(src, out, anonymize(src, out, terms), analysis)


def test_secrets_are_in_the_original(run):
    """Control: si el original no los contuviera, el test siguiente no probaría nada."""
    text = _everything(run.src)
    assert [s for s in SECRETS if s not in text] == []


@pytest.mark.parametrize("secret", SECRETS)
def test_secret_is_removed(run, secret):
    leaked = secret in _everything(run.out)  # sin "assert x not in y": el diff es enorme
    assert not leaked


def test_public_bodies_are_kept(run):
    text = " ".join(_visible_text(run.out).split())
    assert [k for k in KEPT if k not in text] == []


def test_andorran_suggestions(run):
    aliases = {s.replacement for s in run.analysis.suggestions}
    assert {
        "[PASSAPORT_1]", "[PASSAPORT_2]", "[NRT_1]", "[NRT_2]", "[NUM_CASS_1]",
        "[PERMIS_RESIDENCIA_1]", "[TELEFON_1]", "[ADRECA_1]", "[IBAN_1]", "[MATRICULA_1]",
        "[PROCEDIMENT_1]", "[CORREU_1]",
    } <= aliases  # fmt: skip


def test_no_leftovers_reported(run):
    assert not [n for n in run.report.notices if n.is_leak]


@pytest.mark.skipif(not ner.is_available(), reason="modelo NER no instalado")
@pytest.mark.parametrize("suffix", [".docx", ".pdf"])
def test_names_suggested_without_user_list(tmp_path, suffix):
    """Sin lista del usuario: personas y empresa sugeridas, organismos andorranos no."""
    src = BUILDERS[suffix](tmp_path / f"demanda{suffix}")
    named = [s for s in analyze(src, [], CATALAN).suggestions if s.label in ner.LABELS.values()]
    forms = {f for s in named for f in s.forms}
    assert {"Pere Riba i Montané", "Laura Fontanals Pujol", "Núria Serra"} <= forms
    assert any("PIRINEU" in f.upper() for f in forms)
    public = ("CASS", "ANDORRA", "BATLLIA", "COMÚ", "VELLA", "BUTLLETÍ", "POLICIA")
    assert [f for f in forms if any(p in f.upper() for p in public)] == []
