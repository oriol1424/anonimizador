"""Estimación de tiempo, progreso global y salida Markdown."""

import time
from pathlib import Path

from anonimizador.core import estimate
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import anonymize, document_info, output_formats


def test_estimates_grow_with_the_work():
    word = estimate.Workload("docx", chars=140_000)
    scanned = estimate.Workload("pdf", pages=80, scanned=80)
    assert estimate.total(word) < 60  # Word de 80 págs: menos de un minuto
    assert estimate.total(scanned) > 8 * 60  # 80 págs escaneadas: varios minutos
    assert estimate.analysis(scanned)["read"] > estimate.analysis(scanned)["detect"]
    assert "export" in estimate.anonymization(scanned, ".md")
    assert "export" not in estimate.anonymization(scanned, ".pdf")


def test_document_info_counts_pages_images_and_chars(demanda_ca, demanda_pdf):
    word = document_info(demanda_ca)
    assert word.kind == "docx" and word.chars > 500
    pdf = document_info(demanda_pdf)
    assert (pdf.pages, pdf.scanned) == (2, 1)


def test_markdown_output_keeps_structure_and_is_verified(demanda_ca, tmp_path: Path):
    assert ".md" in output_formats(demanda_ca)
    out = tmp_path / "sortida.md"
    report = anonymize(demanda_ca, out, [Term("Joan Puig i Ferrer", "[CLIENT_1]")])
    md = out.read_text(encoding="utf-8")
    assert md.startswith("# AL JUTJAT DE PRIMERA INSTÀNCIA")
    assert "| Demandat | Construccions del Vallès SL |" in md and "| --- | --- |" in md
    assert "**[CLIENT_1]**" in md and "Puig" not in md
    assert not [n for n in report.notices if n.is_leak]


def test_pdf_markdown_joins_broken_lines(demanda_pdf, tmp_path: Path):
    out = tmp_path / "sortida.md"
    anonymize(demanda_pdf, out, [Term("Joan Puig i Ferrer", "[CLIENT_1]")])
    md = out.read_text(encoding="utf-8")
    assert "Puig" not in md and "[CLIENT_1]" in md


def test_progress_page_overall_and_time(qtbot):
    from anonimizador.ui.status_pages import ProgressPage

    page = ProgressPage(lambda: None)
    qtbot.addWidget(page)
    page.start("progress_anonymizing", ["anonymize", "verify"], "ca", "pages",
               {"anonymize": 90.0, "verify": 10.0})  # fmt: skip
    assert page.percent.text() == "0 %"
    assert "Temps estimat: uns 2 min" == page.eta.text()
    page.update_progress("anonymize", 40, 80)
    assert page.percent.text() == "45 %"  # 90 s × 0,5 de 100 s
    page.update_progress("verify", 5, 10)
    assert page.percent.text() == "95 %"
    assert page.elapsed.text().startswith("Temps transcorregut: 0:0")
    page._started = time.monotonic() - 50  # 50 s para el 95 %: quedan unos segundos
    page._refresh()
    assert page.eta.text() == "Temps restant aproximat: menys d'un minut"
    page.stop()


def test_progress_page_says_it_is_still_working(qtbot):
    from anonimizador.ui.status_pages import STILL_WORKING_AFTER, ProgressPage

    page = ProgressPage(lambda: None)
    qtbot.addWidget(page)
    page.start("progress_analyzing", ["read", "detect"], "ca", "pages", {"read": 10, "detect": 5})
    page._last_event = time.monotonic() - STILL_WORKING_AFTER - 1
    page._tick()
    assert not page.still_working.isHidden() and "continua treballant" in page.still_working.text()
    page.update_progress("read", 1, 3)
    assert page.still_working.isHidden()
    page.stop()
