"""Idiomas de los documentos. Por defecto, catalán (la práctica totalidad de los casos)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    code: str
    name: str
    # Nombre visible de cada tipo de dato detectado por reglas -> alias "[NOMBRE_1]".
    # Sin tildes ni caracteres especiales para que los alias sobrevivan a cualquier IA.
    labels: dict[str, str]
    # Opciones del desplegable "Sustituir por" ({n} = número correlativo).
    presets: tuple[str, ...]


CATALAN = Language(
    code="ca",
    name="Català",
    labels={
        "DNI": "DNI",
        "NIE": "NIE",
        "CIF": "NIF_EMPRESA",
        "IBAN": "IBAN",
        "TELEFONO": "TELEFON",
        "EMAIL": "CORREU",
        "MATRICULA": "MATRICULA",
        "PROCEDIMIENTO": "PROCEDIMENT",
    },
    presets=(
        "[PERSONA_{n}]",
        "[CLIENT_{n}]",
        "[PART_CONTRARIA_{n}]",
        "[EMPRESA_{n}]",
        "[ADRECA_{n}]",
        "[ADVOCAT_{n}]",
        "***",
    ),
)

SPANISH = Language(
    code="es",
    name="Castellano",
    labels={
        "DNI": "DNI",
        "NIE": "NIE",
        "CIF": "CIF",
        "IBAN": "IBAN",
        "TELEFONO": "TELEFONO",
        "EMAIL": "EMAIL",
        "MATRICULA": "MATRICULA",
        "PROCEDIMIENTO": "PROCEDIMIENTO",
    },
    presets=(
        "[PERSONA_{n}]",
        "[CLIENTE_{n}]",
        "[PARTE_CONTRARIA_{n}]",
        "[EMPRESA_{n}]",
        "[DIRECCION_{n}]",
        "[ABOGADO_{n}]",
        "***",
    ),
)

LANGUAGES = {lang.code: lang for lang in (CATALAN, SPANISH)}
DEFAULT_LANGUAGE = CATALAN


def fill_preset(template: str, used: set[str]) -> str:
    """ "[CLIENT_{n}]" -> "[CLIENT_1]" o el primer número libre."""
    if "{n}" not in template:
        return template
    n = 1
    while template.format(n=n) in used:
        n += 1
    return template.format(n=n)


def get_language(code: str) -> Language:
    try:
        return LANGUAGES[code]
    except KeyError:
        raise ValueError(f"Idioma no soportado: {code}") from None
