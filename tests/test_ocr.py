import pymupdf

from anonimizador.core import ocr

# Con el clasificador de orientación activo, la primera línea de este párrafo se leía
# girada 180° ("24 ... 025 Barcelona") y el nombre y el DNI quedaban sin borrar.
PARAGRAPH = (
    "24. En Marc Puig i Mas, amb DNI 10000024Z i domicili al carrer de la Indústria, 25, "
    "08025 Barcelona, va declarar que el Sr. Joan Puig i Ferrer li devia 1.500 euros. "
    "La societat Construccions del Vallès SL ho va reconèixer davant el Jutjat de Girona. "
    "El testimoni Pau Font ho confirma."
)


def test_line_is_not_flipped_by_orientation_classifier():
    page = pymupdf.open().new_page()
    page.insert_textbox(pymupdf.Rect(56, 56, 540, 800), PARAGRAPH, fontsize=11)
    pix = page.get_pixmap(dpi=150, colorspace=pymupdf.csGRAY)
    text, _ = ocr.recognize(pymupdf.Pixmap(pymupdf.csRGB, pix)).text_and_boxes()
    assert "Marc Puig i Mas" in text
    assert "10000024Z" in text


def test_read_ahead_is_reused_by_analysis(demanda_pdf, monkeypatch):
    """Lo leído mientras el usuario rellena la lista no se vuelve a leer al analizar."""
    import threading

    from anonimizador.core import pdf_io
    from anonimizador.core.lang import CATALAN
    from anonimizador.core.pipeline import analyze

    ocr.clear_cache()
    pdf_io.read_ahead(demanda_pdf, threading.Event())
    real_run, calls = ocr._run, []
    monkeypatch.setattr(ocr, "_run", lambda *a: calls.append(1) or real_run(*a))
    analyze(demanda_pdf, [], CATALAN)
    assert calls == []


def test_read_ahead_can_be_stopped(demanda_pdf):
    from anonimizador.core.pipeline import read_ahead

    ahead = read_ahead(demanda_pdf)
    ahead.stop()  # no se queda colgado
    assert read_ahead(demanda_pdf.with_suffix(".docx")) is None


def test_blank_scanned_page_does_not_fail(tmp_path):
    from anonimizador.core.matcher import Term
    from anonimizador.core.pipeline import anonymize

    blank = pymupdf.open().new_page().get_pixmap(dpi=100, colorspace=pymupdf.csGRAY)
    doc = pymupdf.open()
    doc.new_page().insert_image(pymupdf.Rect(0, 0, 595, 842), pixmap=blank)
    doc.save(str(tmp_path / "blanc.pdf"))
    report = anonymize(tmp_path / "blanc.pdf", tmp_path / "sortida.pdf", [Term("Joan", "[C]")])
    assert report.total == 0


def _page(lines, scores=()):
    return ocr.OcrPage(
        tuple(
            tuple(ocr.OcrWord(t, pymupdf.Rect(x0, y, x1, y + 20)) for t, x0, x1 in line)
            for y, line in enumerate(lines)
        ),
        tuple(scores),
    )


NORMAL = [
    ("Jo,", 0, 30), ("Joan", 40, 90), ("Puig", 100, 150), ("amb", 160, 200), ("DNI", 210, 250)
]  # fmt: skip


def test_line_with_low_score_is_doubtful():
    page = _page([NORMAL, NORMAL, NORMAL], scores=(0.99, 0.71, 0.98))
    assert page.doubtful_lines() == [1]


def test_wide_line_with_few_letters_is_doubtful():
    """Como "24 … 025" ocupando toda la línea (un nombre y un DNI mal leídos)."""
    page = _page([NORMAL, [("24", 0, 20), ("025", 220, 250)], NORMAL], scores=(0.99, 0.99, 0.99))
    assert page.doubtful_lines() == [1]


def test_clean_page_has_no_doubtful_lines():
    assert _page([NORMAL, NORMAL, NORMAL[:2]], scores=(0.99, 0.98, 0.99)).doubtful_lines() == []
    assert ocr.OcrPage(()).doubtful_lines() == []
