"""Regresiones de la auditoría del 2026-10-11 (docs/AUDITORIA.md). Datos inventados."""

import zipfile
from pathlib import Path

import pymupdf
import pytest
from docx import Document
from docx.shared import Inches

from anonimizador.core.matcher import Matcher, Term
from anonimizador.core.pipeline import anonymize
from anonimizador.core.regex_es import detect

NAME = "Joan Puig i Ferrer"
TERMS = [Term(NAME, "[CLIENT_1]")]


def _zip_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        return "\n".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist())


def _word_with_extras(path: Path) -> Path:
    """Word con texto alternativo, propiedad personalizada y miniatura (como los de Word)."""
    base = path.with_name("base.docx")
    doc = Document()
    doc.add_paragraph(f"En {NAME} compareix.")
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 20, 20), False)
    pix.clear_with(200)
    image = path.with_name("foto.png")
    pix.save(str(image))
    doc.add_picture(str(image), width=Inches(1))
    doc.inline_shapes[0]._inline.docPr.set("descr", f"Foto del DNI de {NAME}")
    doc.save(str(base))
    custom = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://'
        'schemas.openxmlformats.org/officeDocument/2006/custom-properties" xmlns:vt="http://'
        'schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><property fmtid="{D5CD'
        'D505-2E9C-101B-9397-08002B2CF9AE}" pid="2" name="Client">'
        f"<vt:lpwstr>{NAME}</vt:lpwstr></property></Properties>"
    )
    with zipfile.ZipFile(base) as zin, zipfile.ZipFile(path, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = data.replace(b"</Types>", b'<Override PartName="/docProps/custom.xml" '
                                    b'ContentType="application/vnd.openxmlformats-officedocument'
                                    b'.custom-properties+xml"/></Types>')  # fmt: skip
            if item.filename == "_rels/.rels":
                data = data.replace(b"</Relationships>", b'<Relationship Id="rIdC" Type="http:'
                                    b'//schemas.openxmlformats.org/officeDocument/2006/relation'
                                    b'ships/custom-properties" Target="docProps/custom.xml"/>'
                                    b"</Relationships>")  # fmt: skip
            zout.writestr(item, data)
        zout.writestr("docProps/custom.xml", custom)
    return path


@pytest.fixture
def word_out(tmp_path):
    src = _word_with_extras(tmp_path / "doc.docx")
    assert "thumbnail" in _zip_text(src) and "Foto del DNI de Joan" in _zip_text(src)
    out = tmp_path / "out.docx"
    return out, anonymize(src, out, TERMS)


def test_word_alt_text_custom_props_and_thumbnail(word_out):
    out, report = word_out
    text = _zip_text(out)
    assert "Puig" not in text  # ni texto alternativo ni propiedad personalizada
    assert "Foto del DNI de [CLIENT_1]" in text
    with zipfile.ZipFile(out) as z:
        assert not [n for n in z.namelist() if "thumbnail" in n]
    assert not [n for n in report.notices if n.is_leak]


def test_pdf_text_outside_cropbox_is_removed(tmp_path):
    src = tmp_path / "doc.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((56, 72), f"Fora del recorte: {NAME}")
    page.insert_text((56, 400), f"Visible: {NAME}")
    page.set_cropbox(pymupdf.Rect(0, 200, 595, 842))
    doc.save(str(src))
    out = tmp_path / "out.pdf"
    anonymize(src, out, TERMS)
    result = pymupdf.open(str(out))[0]
    result.set_cropbox(result.mediabox)
    assert "Puig" not in result.get_text()


def test_pdf_attachments_are_removed(tmp_path):
    src = tmp_path / "doc.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((56, 72), f"En {NAME} compareix.")
    page.add_file_annot((300, 72), f"DNI de {NAME}".encode(), "nota.txt")
    doc.embfile_add("dades.txt", f"DNI de {NAME}: 12345678Z".encode())
    doc.save(str(src))
    out = tmp_path / "out.pdf"
    report = anonymize(src, out, TERMS)
    result = pymupdf.open(str(out))
    assert result.embfile_count() == 0
    assert not list(result[0].annots())
    assert [n.count for n in report.notices if n.kind == "attachments_removed"] == [2]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("el Sr. Mas va dir", "el Sr. [CLIENT_1] va dir"),
        ("la Sra. Mas i Pons", "la Sra. [CLIENT_1]"),
        ("En Mas va signar", "En [CLIENT_1] va signar"),
        ("un mas antic", "un mas antic"),  # palabra corriente
        ("Mas de Can Pons", "Mas de Can [CLIENT_1]"),  # sin tratamiento: no
    ],
)
def test_short_surnames_after_a_title(text, expected):
    assert Matcher([Term("Pere Mas i Pons", "[CLIENT_1]")]).replace(text) == expected


@pytest.mark.parametrize(
    ("text", "label", "value"),
    [
        ("DNI 12345678z", "DNI", "12345678z"),
        ("NIE x1234567l", "NIE", "x1234567l"),
        ("tel. 81 23 45", "TELEFONO", "81 23 45"),
        ("tel. +376 81 23 45", "TELEFONO", "+376 81 23 45"),
        ("tel. (+376) 812345", "TELEFONO", "(+376) 812345"),
        ("mòbil 376 612 345", "TELEFONO", "376 612 345"),
        ("Data de naixement: 03/04/1980", "NACIMIENTO", "03/04/1980"),
        ("nascut el 3 de març de 1980", "NACIMIENTO", "3 de març de 1980"),
        ("nacida el 12 de mayo de 1975", "NACIMIENTO", "12 de mayo de 1975"),
        ("causa 0001234/2025", "PROCEDIMIENTO", "0001234/2025"),
    ],
)
def test_formats_found_in_the_audit(text, label, value):
    assert (label, value) in [(d.label, d.text) for d in detect(text)]


@pytest.mark.parametrize(
    "text", ["pagar 12345678 a la part", "el 03/04/1980 es va signar", "import de 600.000 euros"]
)
def test_no_false_positives_from_new_rules(text):
    assert [d.label for d in detect(text)] == []


# --- Menores (12-15) ----------------------------------------------------------------------

_CHART = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><c:chart><c:title><c:tx>'
    f"<c:rich><a:p><a:r><a:t>Pagaments de Joan </a:t></a:r><a:r><a:t>Puig i Ferrer</a:t></a:r>"
    "</a:p></c:rich></c:tx></c:title><c:plotArea><c:barChart><c:ser><c:tx><c:strRef><c:strCache>"
    f'<c:pt idx="0"><c:v>{NAME}</c:v></c:pt></c:strCache></c:strRef></c:tx></c:ser>'
    "</c:barChart></c:plotArea></c:chart></c:chartSpace>"
)
_CUSTOM_XML = f'<?xml version="1.0"?><dades><client>{NAME}</client></dades>'
_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"


def _word_with_hidden_places(path: Path) -> Path:
    from docx.oxml import parse_xml

    base = path.with_name("base_menors.docx")
    doc = Document()
    p = doc.add_paragraph("Enllaç: ")
    for piece in ('HYPERLINK "mailto:joan.pu', 'ig@correu.example"'):
        run = p.add_run()
        run._r.append(parse_xml(
            '<w:instrText xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
            f' xml:space="preserve">{piece}</w:instrText>'
        ))  # fmt: skip
    doc.settings.element.append(parse_xml(
        '<w:docVars xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:docVar w:name="Client" w:val="{NAME}"/></w:docVars>'
    ))  # fmt: skip
    doc.save(str(base))
    with zipfile.ZipFile(base) as zin, zipfile.ZipFile(path, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = data.replace(b"</Types>", b'<Override PartName="/word/charts/chart1.xml" '
                                    b'ContentType="application/vnd.openxmlformats-officedocument'
                                    b'.drawingml.chart+xml"/></Types>')  # fmt: skip
            if item.filename == "word/_rels/document.xml.rels":
                data = data.replace(b"</Relationships>", (
                    f'<Relationship Id="rIdG" Type="{_REL}chart" Target="charts/chart1.xml"/>'
                    f'<Relationship Id="rIdX" Type="{_REL}customXml" '
                    'Target="../customXml/item9.xml"/></Relationships>'
                ).encode())  # fmt: skip
            zout.writestr(item, data)
        zout.writestr("word/charts/chart1.xml", _CHART)
        zout.writestr("customXml/item9.xml", _CUSTOM_XML)
    return path


def test_word_charts_custom_xml_doc_vars_and_split_fields(tmp_path):
    src = _word_with_hidden_places(tmp_path / "doc.docx")
    assert _zip_text(src).count("Puig") >= 4
    out = tmp_path / "out.docx"
    terms = [*TERMS, Term("joan.puig@correu.example", "[CORREU_1]", expand=False)]
    report = anonymize(src, out, terms)
    text = _zip_text(out)
    assert "Puig" not in text and "joan.pu" not in text
    assert "[CLIENT_1]" in text and "[CORREU_1]" in text
    assert not [n for n in report.notices if n.is_leak]


def test_pdf_with_text_as_outlines_is_read_with_ocr(tmp_path):
    from anonimizador.core import pdf_io

    page = pymupdf.open().new_page()
    page.insert_text((56, 90), f"En {NAME}, DNI 12345678Z, compareix.", fontsize=16)
    svg = page.get_svg_image(text_as_path=True)
    outlined = pymupdf.open(stream=svg.encode(), filetype="svg")
    src = tmp_path / "corbes.pdf"
    pymupdf.open("pdf", outlined.convert_to_pdf()).save(str(src))
    check = pymupdf.open(str(src))[0]
    assert not check.get_text().strip() and pdf_io.is_image_page(check)

    out = tmp_path / "out.pdf"
    report = anonymize(src, out, TERMS)
    assert "Puig" not in pdf_io.extract_text(out)  # releído con OCR
    assert report.replaced.get("[CLIENT_1]")


def test_ambiguous_surname_is_not_given_to_one_person():
    from anonimizador.core.pipeline import Suggestion, merge_variants

    raw = [Suggestion("PERSONA", "", (f,), 1, True) for f in ("Joan Puig", "Pere Puig", "Puig")]
    assert sorted(s.forms for s in merge_variants(raw)) == [
        ("Joan Puig",), ("Pere Puig",), ("Puig",),
    ]  # fmt: skip
    raw = [Suggestion("PERSONA", "", (f,), 1, True) for f in ("Jordi Casals i Pons", "Casals")]
    assert [s.forms for s in merge_variants(raw)] == [("Jordi Casals i Pons", "Casals")]
