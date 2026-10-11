"""Reglas de privacidad comprobables: sin red y sin texto del documento en la consola."""

import socket

import pymupdf
import pytest

from anonimizador.core import ocr


def test_network_is_blocked_during_tests():
    """La protección de conftest (`no_network`) está activa en todos los tests."""
    with pytest.raises(AssertionError), socket.socket() as s:
        s.connect(("93.184.216.34", 80))


def test_ocr_works_without_network_and_prints_no_text(capfd):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((56, 90), "Joan Puig i Ferrer, DNI 12345678Z", fontsize=14)
    text = ocr.recognize(ocr.render(page)).text_and_boxes()[0]
    blank = doc.new_page()  # página vacía: antes RapidOCR avisaba por consola
    ocr.recognize(ocr.render(blank))
    assert "Puig" in text
    out, err = capfd.readouterr()
    assert "Puig" not in out + err and "12345678Z" not in out + err
    assert "WARNING" not in out + err
