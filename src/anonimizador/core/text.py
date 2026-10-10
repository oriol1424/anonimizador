"""Normalización de texto que conserva las posiciones de cada carácter."""

import unicodedata


def _fold_char(char: str) -> str:
    base = "".join(c for c in unicodedata.normalize("NFD", char) if not unicodedata.combining(c))
    folded = base.lower()
    return folded if len(folded) == 1 else char


def fold(text: str) -> str:
    """Minúsculas y sin tildes, con la MISMA longitud que la entrada.

    Mantener la longitud permite buscar sobre el texto normalizado y usar los
    offsets directamente sobre el original.
    """
    return "".join(_fold_char(c) for c in text)
