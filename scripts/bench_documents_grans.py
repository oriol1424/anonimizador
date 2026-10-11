"""Mide tiempos con documentos grandes (datos inventados).

Sin tracemalloc: ralentiza mucho el código Python y falseaba los tiempos (2026-10-11).
"""

import os
import sys
import time
from pathlib import Path

import pymupdf
from docx import Document

from anonimizador.core.lang import CATALAN
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import analyze, anonymize

OUT = Path(sys.argv[1])
SCANNED_PAGES = int(sys.argv[2]) if len(sys.argv) > 2 else 5
FIRST = ["Jordi", "Núria", "Pere", "Laia", "Marc", "Anna", "Oriol", "Marta", "Pau", "Clara"]
LAST = ["Casals", "Ferrer", "Puig", "Vila", "Soler", "Roca", "Pons", "Serra", "Mas", "Font"]


def paragraph(i: int) -> str:
    a = f"{FIRST[i % 10]} {LAST[(i * 3) % 10]} i {LAST[(i * 7) % 10]}"
    return (
        f"{i}. En {a}, amb DNI {10000000 + i}Z i domicili al carrer de la Indústria, {i % 90 + 1}, "
        f"08025 Barcelona, va declarar que el Sr. Joan Puig i Ferrer li devia 1.500 euros. "
        f"La societat Construccions del Vallès SL ho va reconèixer davant el Jutjat de Girona. "
        f"El testimoni {FIRST[(i + 4) % 10]} {LAST[(i + 5) % 10]} ho confirma."
    )


def build_docx(path: Path, pages: int) -> None:
    doc = Document()
    for i in range(pages * 6):  # ~6 párrafos largos por página
        doc.add_paragraph(paragraph(i))
    doc.save(str(path))


def build_pdf(path: Path, pages: int) -> None:
    doc = pymupdf.open()
    for p in range(pages):
        page = doc.new_page()
        rect = pymupdf.Rect(56, 56, 540, 800)
        page.insert_textbox(rect, "\n\n".join(paragraph(p * 6 + k) for k in range(6)), fontsize=10)
    doc.save(str(path))


def build_scanned(path: Path, pages: int) -> None:
    doc = pymupdf.open()
    for p in range(pages):
        src = pymupdf.open()
        sp = src.new_page()
        sp.insert_textbox(
            pymupdf.Rect(56, 56, 540, 800),
            "\n\n".join(paragraph(p * 6 + k) for k in range(6)),
            fontsize=11,
        )
        page = doc.new_page()
        page.insert_image(page.rect, pixmap=sp.get_pixmap(dpi=150, colorspace=pymupdf.csGRAY))
    doc.save(str(path))


def run(name: str, src: Path, out_suffix: str) -> None:
    terms = [Term("Joan Puig i Ferrer", "[CLIENT_1]")]
    t0 = time.time()
    analysis = analyze(src, terms, CATALAN)
    t1 = time.time()
    for s in analysis.suggestions:
        terms.extend(s.to_terms())
    out = OUT / f"{name}_out{out_suffix}"
    report = anonymize(src, out, terms)
    t2 = time.time()
    print(
        f"{name}: anàlisi {t1 - t0:.1f}s, anonimització+verificació {t2 - t1:.1f}s, "
        f"{len(analysis.suggestions)} suggeriments, {report.total} substitucions, "
        f"sortida {os.path.getsize(out) / 1e6:.1f} MB, "
        f"avisos {[n.kind for n in report.notices]}",
        flush=True,
    )


if __name__ == "__main__":
    build_docx(OUT / "big.docx", 80)
    run("word_80p", OUT / "big.docx", ".docx")
    build_pdf(OUT / "big.pdf", 80)
    run("pdf_text_80p", OUT / "big.pdf", ".pdf")
    build_scanned(OUT / "scan.pdf", SCANNED_PAGES)
    run(f"pdf_escanejat_{SCANNED_PAGES}p", OUT / "scan.pdf", ".pdf")
