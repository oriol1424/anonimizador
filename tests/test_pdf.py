"""PDF: borrado real en páginas con texto y en páginas escaneadas (OCR).

El OCR tarda unos segundos por página: el PDF se anonimiza una sola vez por módulo.
"""

from dataclasses import dataclass
from pathlib import Path

import pymupdf
import pytest
from generar_corpus import build_demanda_pdf_ca

from anonimizador.core import ocr, pdf_io
from anonimizador.core.lang import CATALAN
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import AnonymizerError, analyze, anonymize

USER_TERMS = [
    Term("Joan Puig i Ferrer", "[CLIENT_1]"),
    Term("Construccions del Vallès SL", "[EMPRESA_1]"),
    Term("Montserrat Soler i Vidal", "[ADVOCAT_1]"),
    Term("Martí d'Orriols", "[PART_CONTRARIA_1]"),
    Term("Marcel·lí Roca", "[PERSONA_1]"),
    Term("Anna Vila", "[PERSONA_2]"),
]

SECRETS = [
    "Joan", "Puig", "Ferrer", "Vallès", "VALLÈS", "Montserrat", "Orriols", "Marcel",
    "Roca", "Anna Vila", "12345678Z", "B12345674", "2100 0418", "972 123 456", "joan.puig",
    "soler-associats", "1234 BCD", "1234/2025",
]  # fmt: skip


def _everything(path: Path) -> str:
    """Todo lo que cualquier herramienta podría leer del PDF (texto, notas, enlaces, metadatos)."""
    doc = pymupdf.open(str(path))
    parts = [pdf_io.extract_text(path), str(doc.metadata), doc.get_xml_metadata()]
    parts += [page.get_text("rawdict").__repr__() for page in doc]
    doc.close()
    return "\n".join(parts)


@dataclass
class Run:
    src: Path
    out: Path
    report: object
    analysis: object
    src_text: str
    out_text: str


@pytest.fixture(scope="module")
def run(tmp_path_factory) -> Run:
    folder = tmp_path_factory.mktemp("pdf")
    src = build_demanda_pdf_ca(folder / "demanda_ca.pdf")
    terms = list(USER_TERMS)
    analysis = analyze(src, terms, CATALAN)
    for s in analysis.suggestions:
        terms.extend(s.to_terms())
    out = folder / "sortida.pdf"
    report = anonymize(src, out, terms)
    return Run(src, out, report, analysis, _everything(src), _everything(out))


def test_secrets_are_readable_in_the_original(run):
    """Control: si el original no los contuviera, el test siguiente no probaría nada."""
    assert all(secret in run.src_text for secret in SECRETS)


@pytest.mark.parametrize("secret", SECRETS)
def test_secret_is_really_removed(run, secret):
    """Incluye la página escaneada: `_everything` la vuelve a leer con OCR."""
    assert secret not in run.out_text


def test_rest_of_text_is_kept(run):
    text = pymupdf.open(str(run.out))[0].get_text()
    for kept in [
        "AL JUTJAT DE PRIMERA INST",
        "va subscriure un contracte amb",
        "major d'edat i viu al carrer major del poble.",
        "no ha pagat.",
        "Demandat",
    ]:
        assert kept in text
    for alias in ["[CLIENT_1]", "[EMPRESA_1]", "[PART_CONTRARIA_1]", "[DNI_1]", "[IBAN_1]"]:
        assert alias in text


def test_name_split_across_lines_is_removed(run):
    """ "J. Puig" al final de una línea y "Ferrer" al principio de la siguiente."""
    page = pymupdf.open(str(run.out))[0]
    fer = page.search_for("El pagament el va fer")[0]
    compte = page.search_for("al compte")[0]
    aliases = page.search_for("[CLIENT_1]")
    # El alias ocupa el sitio de "J. Puig": misma línea y a la derecha de "fer".
    assert any(abs(a.y1 - fer.y1) < 2 and a.x0 >= fer.x1 for a in aliases)
    # En la línea siguiente no queda nada delante de "al compte".
    words_before = [
        w for w in page.get_text("words") if abs(w[3] - compte.y1) < 2 and w[2] <= compte.x0
    ]
    assert words_before == []


def test_table_lines_are_kept(run):
    before = len(pymupdf.open(str(run.src))[0].get_drawings())
    after = len(pymupdf.open(str(run.out))[0].get_drawings())
    assert after == before


def test_scanned_page_is_read_and_anonymized(run):
    """Página escaneada: el OCR sobre la imagen resultante ya no ve los datos."""
    ocr_text, _ = ocr.recognize(ocr.render(pymupdf.open(str(run.out))[1])).text_and_boxes()
    for kept in ["ANNEX 1", "he rebut de", "1.500 euros", "bestreta", "Girona, 3 de març"]:
        assert kept in ocr_text
    for gone in ["Puig", "Ferrer", "12345678Z", "Orriols"]:
        assert gone not in ocr_text
    assert "[CLIENT_1]" in ocr_text


def test_scanned_page_has_anonymized_text_layer(run):
    layer = pymupdf.open(str(run.out))[1].get_text()
    assert "[CLIENT_1]" in layer and "he rebut de" in layer
    assert "Puig" not in layer


def test_scanned_page_dni_is_suggested(run):
    dni = next(s for s in run.analysis.suggestions if s.label == "DNI")
    assert dni.count == 2  # una en la página de texto y otra en la escaneada


def test_ocr_notice_and_no_leftovers(run):
    assert [n.count for n in run.report.notices if n.kind == "ocr"] == [1]
    assert not [n for n in run.report.notices if n.kind == "leftovers"]


def test_pdf_to_txt_in_reading_order(demanda_pdf, tmp_path):
    out = tmp_path / "sortida.txt"
    anonymize(demanda_pdf, out, USER_TERMS)
    text = out.read_text(encoding="utf-8")
    assert "El pagament el va fer [CLIENT_1] al compte" in " ".join(text.split())
    assert "En [CLIENT_1], major d'edat" in text
    assert "Jo, [CLIENT_1], amb DNI" in text  # página escaneada, vía OCR
    assert "Puig" not in text
    assert not list(tmp_path.glob("*.tmp.pdf"))


def test_pdf_cannot_be_saved_as_docx(demanda_pdf, tmp_path):
    with pytest.raises(AnonymizerError) as err:
        anonymize(demanda_pdf, tmp_path / "x.docx", USER_TERMS)
    assert err.value.kind == "unsupported_output"


def test_encrypted_pdf_gives_clear_error(demanda_pdf, tmp_path):
    locked = tmp_path / "locked.pdf"
    doc = pymupdf.open(str(demanda_pdf))
    doc.save(str(locked), encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="x", owner_pw="y")
    with pytest.raises(AnonymizerError) as err:
        analyze(locked, USER_TERMS)
    assert err.value.kind == "encrypted"


def _misread_first_ocr(monkeypatch):
    """El primer OCR lee mal la línea de la firma (como pasaba con el clasificador de
    orientación); los siguientes OCR la leen bien."""
    real = ocr.recognize
    calls = []

    def fake(pix):
        page = real(pix)
        calls.append(1)
        if len(calls) > 1:
            return page
        garbled = tuple(
            tuple(ocr.OcrWord(w.text.replace("u", "v").replace("e", "c"), w.rect) for w in line)
            if any(w.text.startswith("Signat") for w in line)
            else line
            for line in page.lines
        )
        return ocr.OcrPage(garbled)

    monkeypatch.setattr(ocr, "recognize", fake)


def test_scanned_verification_fixes_what_first_ocr_missed(demanda_pdf, tmp_path, monkeypatch):
    _misread_first_ocr(monkeypatch)
    out = tmp_path / "sortida.pdf"
    report = anonymize(demanda_pdf, out, USER_TERMS)
    monkeypatch.undo()
    ocr_text, _ = ocr.recognize(ocr.render(pymupdf.open(str(out))[1])).text_and_boxes()
    assert "Signat" in ocr_text
    assert "Puig" not in ocr_text and "Ferrer" not in ocr_text
    assert not [n for n in report.notices if n.is_leak]


def test_scanned_leftovers_are_reported_with_page(demanda_pdf, tmp_path, monkeypatch):
    _misread_first_ocr(monkeypatch)
    real_erase = pdf_io._erase
    erase_calls = []

    def erase_only_first(pix, boxes, matches):
        erase_calls.append(1)
        return real_erase(pix, boxes, matches) if len(erase_calls) == 1 else []

    monkeypatch.setattr(pdf_io, "_erase", erase_only_first)
    report = anonymize(demanda_pdf, tmp_path / "sortida.pdf", USER_TERMS)
    leak = next(n for n in report.notices if n.kind == "leftovers_scan")
    assert leak.pages == "2"
    assert "pàgines escanejades 2" in leak.message(CATALAN)
    assert len(erase_calls) == 1 + pdf_io.MAX_FIX_ROUNDS
