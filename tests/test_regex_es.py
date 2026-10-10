import pytest

from anonimizador.core.regex_es import detect


@pytest.mark.parametrize(
    ("text", "label", "value"),
    [
        ("con DNI 12345678Z en", "DNI", "12345678Z"),
        ("con DNI 12.345.678-Z en", "DNI", "12.345.678-Z"),
        ("NIE X1234567L.", "NIE", "X1234567L"),
        ("CIF B12345674,", "CIF", "B12345674"),
        ("cuenta ES91 2100 0418 4502 0005 1332.", "IBAN", "ES91 2100 0418 4502 0005 1332"),
        ("cuenta ES9121000418450200051332.", "IBAN", "ES9121000418450200051332"),
        ("llame al 612 345 678 hoy", "TELEFONO", "612 345 678"),
        ("llame al +34 912 34 56 78", "TELEFONO", "+34 912 34 56 78"),
        ("escriba a ana.lopez@correo.example.", "EMAIL", "ana.lopez@correo.example"),
        ("vehículo 1234 BCD rojo", "MATRICULA", "1234 BCD"),
        ("autos 1234/2025 del juzgado", "PROCEDIMIENTO", "1234/2025"),
    ],
)
def test_detects(text, label, value):
    found = [(d.label, d.text) for d in detect(text)]
    assert (label, value) in found


@pytest.mark.parametrize(
    ("text", "address"),
    [
        ("domicili al carrer de la Indústria, 45, 3r 2a, 08025 Barcelona, compareix",
         "carrer de la Indústria, 45, 3r 2a, 08025 Barcelona"),
        ("resideix a l'avinguda Diagonal, 640, de Barcelona.",
         "avinguda Diagonal, 640, de Barcelona"),
        ("a la plaça Major, 3, de Vic.", "plaça Major, 3, de Vic"),
        ("al passeig de Gràcia, 92, principal, està", "passeig de Gràcia, 92, principal"),
        ("a la carretera de Sant Sadurní, km 3, de Vilafranca del Penedès.",
         "carretera de Sant Sadurní, km 3, de Vilafranca del Penedès"),
        ("C/ Major, s/n, de Tremp.", "C/ Major, s/n, de Tremp"),
        ("Av. Diagonal 640", "Av. Diagonal 640"),
        ("carrer del Dr. Trueta, 12", "carrer del Dr. Trueta, 12"),
        ("en la calle Mayor 5, 2º B, 28013 Madrid.", "calle Mayor 5, 2º B, 28013 Madrid"),
    ],
)  # fmt: skip
def test_detects_addresses(text, address):
    assert ("DIRECCION", address) in [(d.label, d.text) for d in detect(text)]


@pytest.mark.parametrize(
    "text",
    [
        "La part és major d'edat i viu al carrer major del poble. El 2025 va marxar.",
        "Per via 3 de recurs.",
        "Vistos els articles 248 i següents de la Llei d'Enjudiciament Civil.",
    ],
)
def test_no_address_false_positives(text):
    assert not [d for d in detect(text) if d.label == "DIRECCION"]


def test_invalid_iban_is_ignored():
    assert not [d for d in detect("ES00 2100 0418 4502 0005 1332") if d.label == "IBAN"]


def test_no_false_positives_in_plain_text():
    assert detect("El artículo 24 de la Constitución, año 2025, página 12.") == []
