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
