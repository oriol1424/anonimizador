"""Normalización de texto que conserva las posiciones de cada carácter."""

import unicodedata
from functools import lru_cache

# Apóstrofos tipográficos (Word los pone solos: d’Orriols) -> apóstrofo simple.
_APOSTROPHES = {"’": "'", "‘": "'", "ʼ": "'", "´": "'"}
# Punto volado del catalán (col·legi, Marcel·lí): variantes -> U+00B7.
_MIDDLE_DOTS = {"‧": "·", "⋅": "·", "∙": "·"}


# Caracteres que algunos PDF dan al extraer el texto (fuentes sin tabla Unicode: el
# espacio sale como ""). Rompen Word/XML y el .txt, y separan las palabras sin ser
# espacios: «JoanPuig» no coincidía con la lista y el nombre se filtraba. Se cambian
# uno por uno (misma longitud: las cajas de cada letra siguen alineadas).
_UNSAFE = {c: " " for c in (*range(0x00, 0x09), 0x0B, 0x0C, *range(0x0E, 0x20), 0x7F)}
_UNSAFE |= {c: "�" for c in (*range(0xD800, 0xE000), 0xFFFE, 0xFFFF)}


def clean_text(text: str) -> str:
    """Controles -> espacio; suplentes sueltos y no-caracteres -> «�». Misma longitud."""
    return text.translate(_UNSAFE)


@lru_cache(maxsize=4096)
def _fold_char(char: str) -> str:
    if char in _APOSTROPHES:
        return _APOSTROPHES[char]
    if char in _MIDDLE_DOTS:
        return _MIDDLE_DOTS[char]
    base = "".join(c for c in unicodedata.normalize("NFD", char) if not unicodedata.combining(c))
    folded = base.lower()
    return folded if len(folded) == 1 else char


def fold(text: str) -> str:
    """Minúsculas, sin tildes y con apóstrofos unificados, con la MISMA longitud que la entrada.

    Mantener la longitud permite buscar sobre el texto normalizado y usar los
    offsets directamente sobre el original.
    """
    return "".join(_fold_char(c) for c in text)
