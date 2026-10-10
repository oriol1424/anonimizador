"""Genera documentos de prueba con datos INVENTADOS.

Uso manual:  python tests/corpus/generar_corpus.py  -> crea tests/corpus/demanda_ficticia.docx
Cubre los casos difíciles: nombres partidos en varios runs con distinto formato, tablas,
cabecera, pie, comentarios, control de cambios, hipervínculos mailto y metadatos.
"""

from pathlib import Path

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def _add_hyperlink(paragraph, url: str, text: str) -> None:
    r_id = paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = text
    run.append(t)
    link.append(run)
    paragraph._p.append(link)


def _add_tracked_deletion(paragraph, text: str, author: str) -> None:
    deletion = OxmlElement("w:del")
    deletion.set(qn("w:id"), "1")
    deletion.set(qn("w:author"), author)
    deletion.set(qn("w:date"), "2026-01-01T00:00:00Z")
    run = OxmlElement("w:r")
    del_text = OxmlElement("w:delText")
    del_text.text = text
    run.append(del_text)
    deletion.append(run)
    paragraph._p.append(deletion)


def build_demanda(path: Path) -> Path:
    doc = Document()
    doc.core_properties.author = "Laura Martín Ruiz"
    doc.core_properties.last_modified_by = "Laura Martín Ruiz"
    doc.core_properties.title = "Demanda Juan Pérez García contra Construcciones Levante SL"

    section = doc.sections[0]
    section.header.paragraphs[0].text = "Despacho Martín & Asociados — Letrada Laura Martín Ruiz"
    section.footer.paragraphs[0].text = "Tel. 612 345 678 · info@martin-asociados.example"

    doc.add_heading("AL JUZGADO DE PRIMERA INSTANCIA", level=1)

    p = doc.add_paragraph("Don ")
    p.add_run("Juan ").bold = True
    p.add_run("Pé").bold = True
    p.add_run("rez García").italic = True
    p.add_run(", mayor de edad, con DNI 12345678Z y domicilio en Calle Mayor 5, Valencia, ")
    p.add_run("actuando en su propio nombre, ante el Juzgado comparece y DICE:")

    doc.add_paragraph(
        "Que el Sr. Pérez suscribió contrato con CONSTRUCCIONES LEVANTE SL (CIF B12345674) "
        "en el procedimiento 1234/2025. J. Pérez García abonó las cantidades en la cuenta "
        "ES91 2100 0418 4502 0005 1332."
    )

    p = doc.add_paragraph("Contacto del demandante:\t")
    p.add_run("Juan")
    p.add_run().add_tab()
    p.add_run("Pérez García")

    p = doc.add_paragraph("Correo: ")
    _add_hyperlink(p, "mailto:juan.perez@correo.example", "juan.perez@correo.example")

    p = doc.add_paragraph("Texto revisado. ")
    _add_tracked_deletion(p, "Antes ponía Juan Pérez García", "Laura Martín Ruiz")

    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Demandado"
    table.cell(0, 1).text = "Construcciones Levante SL"
    table.cell(1, 0).text = "Vehículo"
    table.cell(1, 1).text = "Matrícula 1234 BCD, conductor Ana López"

    commented = doc.add_paragraph("Párrafo con comentario.")
    doc.add_comment(
        commented.runs,
        text="Confirmar con Juan Pérez García",
        author="Laura Martín Ruiz",
        initials="LM",
    )

    doc.add_paragraph("La parte es mayor de edad y vive en la calle mayor del pueblo.")
    doc.save(str(path))
    return path


if __name__ == "__main__":
    out = build_demanda(Path(__file__).with_name("demanda_ficticia.docx"))
    print(f"Creado {out}")
