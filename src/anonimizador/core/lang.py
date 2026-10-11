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
    # Texto de la página en blanco que sustituye a una página que no se pudo procesar.
    failed_page: str = "[Pàgina {n} no processada]"


CATALAN = Language(
    code="ca",
    name="Català",
    labels={
        "DNI": "DNI",
        "NIE": "NIE",
        "CIF": "NIF_EMPRESA",
        "NRT": "NRT",
        "PASAPORTE": "PASSAPORT",
        "CASS": "NUM_CASS",
        "RESIDENCIA": "PERMIS_RESIDENCIA",
        "NACIMIENTO": "DATA_NAIXEMENT",
        "IBAN": "IBAN",
        "TELEFONO": "TELEFON",
        "EMAIL": "CORREU",
        "MATRICULA": "MATRICULA",
        "PROCEDIMIENTO": "PROCEDIMENT",
        "DIRECCION": "ADRECA",
        "PERSONA": "PERSONA",
        "EMPRESA": "EMPRESA",
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
    failed_page="[Pàgina {n} no processada]",
)

SPANISH = Language(
    code="es",
    name="Castellano",
    labels={
        "DNI": "DNI",
        "NIE": "NIE",
        "CIF": "CIF",
        "NRT": "NRT",
        "PASAPORTE": "PASAPORTE",
        "CASS": "NUM_CASS",
        "RESIDENCIA": "PERMISO_RESIDENCIA",
        "NACIMIENTO": "FECHA_NACIMIENTO",
        "IBAN": "IBAN",
        "TELEFONO": "TELEFONO",
        "EMAIL": "EMAIL",
        "MATRICULA": "MATRICULA",
        "PROCEDIMIENTO": "PROCEDIMIENTO",
        "DIRECCION": "DIRECCION",
        "PERSONA": "PERSONA",
        "EMPRESA": "EMPRESA",
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
    failed_page="[Página {n} no procesada]",
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
