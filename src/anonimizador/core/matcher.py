"""Búsqueda de los términos a anonimizar (y sus variantes) dentro de un texto.

Pensado para nombres catalanes y castellanos: "Joan Puig i Ferrer", "Martí d'Orriols",
"Marcel·lí Soler", "Juan Pérez García".
"""

import re
from dataclasses import dataclass

from anonimizador.core.text import fold

# Partículas que no identifican a nadie por sí solas (catalán + castellano).
CONNECTORS = {
    "de", "del", "dels", "la", "las", "les", "los", "el", "y", "e", "i", "da", "van", "von",
}  # fmt: skip
# Conjunción entre apellidos: "Puig i Ferrer" == "Puig Ferrer".
CONJUNCTIONS = {"i", "y"}
ELISIONS = ("d'", "l'")
LEGAL_FORMS = {
    "sl", "s.l.", "slu", "s.l.u.", "sa", "s.a.", "sau", "s.a.u.", "sll", "s.l.l.",
    "scp", "s.c.p.", "cb", "c.b.", "sc", "s.c.", "coop.", "sccl", "s.c.c.l.",
    "sociedad", "societat", "limitada", "anonima", "anònima", "cooperativa",
}  # fmt: skip

# Límites de palabra: el punto volado forma parte de la palabra (Marcel·lí), el apóstrofo no
# (d'Orriols -> "Orriols" es una palabra).
_WORD = r"[\w·]"


@dataclass(frozen=True)
class Term:
    """Un texto a anonimizar y su sustituto."""

    original: str
    replacement: str
    expand: bool = True  # generar variantes ("Sr. Puig", "J. Puig"...)
    source: str = "usuario"
    # No anonimizar nunca (p. ej. el nombre de la abogada): se busca para que nadie lo
    # sustituya ni en parte, pero no se cambia.
    keep: bool = False


def keep_term(text: str) -> Term:
    return Term(text, text, source="keep", keep=True)


@dataclass(frozen=True)
class Match:
    start: int
    end: int
    text: str
    replacement: str
    source: str


def _strip_elision(token: str) -> str:
    folded = fold(token)
    for prefix in ELISIONS:
        if folded.startswith(prefix) and len(token) > len(prefix):
            return token[len(prefix) :]
    return token


def _starts_upper(text: str) -> bool:
    stripped = _strip_elision(text)
    return bool(stripped) and stripped[0].isupper()


def variants(name: str) -> list[str]:
    """Formas parciales con las que suele aparecer un nombre en un escrito.

    "Joan Puig i Ferrer" -> "Joan Puig", "Puig i Ferrer", "J. Puig i Ferrer", "Puig", "Ferrer".
    "Martí d'Orriols"    -> "M. d'Orriols", "d'Orriols", "Orriols".
    """
    tokens = name.split()
    if len(tokens) < 2 or not any(c.isalpha() for c in name):
        return []

    def is_connector(token: str) -> bool:
        return fold(token) in CONNECTORS

    def usable(token: str) -> bool:
        return not is_connector(token) and fold(token) not in LEGAL_FORMS

    found: set[str] = set()
    n = len(tokens)
    for i in range(n):
        for j in range(i + 2, n + 1):
            seq = tokens[i:j]
            if j - i == n or is_connector(seq[0]) or is_connector(seq[-1]):
                continue
            if any(usable(t) for t in seq):
                found.add(" ".join(seq))
    if tokens[0][0].isalpha():
        found.add(f"{tokens[0][0]}. {' '.join(tokens[1:])}")
    for token in tokens[1:]:
        for form in {token, _strip_elision(token)}:
            if len(_strip_elision(form)) >= 4 and usable(form) and _starts_upper(form):
                found.add(form)
    return sorted(found)


def _key(text: str) -> str:
    folded = re.sub(r"\s+(?:i|y)(?=\s)", " ", fold(text))
    return re.sub(r"\s+", "", folded)


def _pattern(text: str) -> str:
    parts: list[str] = []
    for token in text.split():
        folded = fold(token)
        if parts and folded in CONJUNCTIONS:
            continue  # cubierta por el separador opcional
        if parts:
            parts.append(r"\s*" if parts[-1].endswith(r"\.") else r"\s+(?:[iy]\s+)?")
        parts.append(re.escape(folded))
    return rf"(?<!{_WORD})" + "".join(parts) + rf"(?!{_WORD})"


class Matcher:
    """Encuentra todas las apariciones de una lista de términos.

    - Ignora mayúsculas, tildes y el tipo de apóstrofo ("PUIG" encuentra "Puig").
    - "Puig i Ferrer" y "Puig Ferrer" se consideran el mismo nombre.
    - Las variantes derivadas solo se aceptan si empiezan en mayúscula, para que
      "Major" (de "Carrer Major") no sustituya "major d'edat".
    - Si una variante es común a dos términos con sustitutos distintos (dos
      personas apellidadas Puig), no se aplica y se informa en `ambiguous`.
    - Los términos `keep` (no anonimizar nunca) ocupan su sitio pero no se sustituyen:
      "Montserrat Soler i Vidal" queda intacto aunque otro término tenga la variante
      "Soler". De ellos solo se protegen el nombre completo y las variantes de dos o más
      palabras: un apellido suelto podría ser de otra persona (ante la duda, anonimizar).
      Si un texto está a la vez en la lista del usuario y en `keep`, gana la lista.
    """

    def __init__(self, terms: list[Term]):
        self.ambiguous: set[str] = set()
        entries: dict[str, tuple[Term, bool, str]] = {}
        derived: dict[str, list[tuple[Term, str]]] = {}

        ordered = [t for t in terms if not t.keep] + [t for t in terms if t.keep]
        for term in ordered:
            if not term.original.strip():
                continue
            entries.setdefault(_key(term.original), (term, False, term.original))
        for term in ordered:
            if not term.expand:
                continue
            for variant in variants(term.original):
                if term.keep and len(variant.split()) < 2:
                    continue
                derived.setdefault(_key(variant), []).append((term, variant))
        for key, options in derived.items():
            if key in entries:
                continue
            if len({t.replacement for t, _ in options}) > 1:
                self.ambiguous.add(options[0][1])
                continue
            term, variant = options[0]
            entries[key] = (term, True, variant)

        self._entries = entries
        self._regex = None
        if entries:
            texts = sorted((v[2] for v in entries.values()), key=len, reverse=True)
            self._regex = re.compile("|".join(_pattern(t) for t in texts))

    def find(self, text: str, include_kept: bool = False) -> list[Match]:
        """Apariciones a sustituir. Con `include_kept`, también las de los términos que
        no se anonimizan (con `source="keep"`)."""
        if self._regex is None:
            return []
        matches = []
        for m in self._regex.finditer(fold(text)):
            entry = self._entries.get(_key(m.group()))
            if entry is None:
                continue
            term, strict_case, _ = entry
            original = text[m.start() : m.end()]
            if strict_case and not _starts_upper(original):
                continue
            if term.keep and not include_kept:
                continue
            matches.append(Match(m.start(), m.end(), original, term.replacement, term.source))
        return matches

    def replace(self, text: str) -> str:
        for m in reversed(self.find(text)):
            text = text[: m.start] + m.replacement + text[m.end :]
        return text
