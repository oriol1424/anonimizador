"""Búsqueda de los términos a anonimizar (y sus variantes) dentro de un texto."""

import re
from dataclasses import dataclass

from anonimizador.core.text import fold

CONNECTORS = {"de", "del", "la", "las", "los", "y", "e", "i", "da", "van", "von"}
LEGAL_FORMS = {
    "sl",
    "s.l.",
    "slu",
    "s.l.u.",
    "sa",
    "s.a.",
    "sau",
    "s.a.u.",
    "sll",
    "s.l.l.",
    "scp",
    "s.c.p.",
    "cb",
    "c.b.",
    "sc",
    "s.c.",
    "coop.",
    "sociedad",
    "limitada",
    "anonima",
}


@dataclass(frozen=True)
class Term:
    """Un texto a anonimizar y su sustituto."""

    original: str
    replacement: str
    expand: bool = True  # generar variantes ("Sr. Pérez", "J. Pérez"...)
    source: str = "usuario"


@dataclass(frozen=True)
class Match:
    start: int
    end: int
    text: str
    replacement: str
    source: str


def variants(name: str) -> list[str]:
    """Formas parciales con las que suele aparecer un nombre en un escrito.

    "Juan Pérez García" -> "Juan Pérez", "Pérez García", "J. Pérez García", "Pérez", "García".
    """
    tokens = name.split()
    if len(tokens) < 2 or not any(c.isalpha() for c in name):
        return []

    def usable(token: str) -> bool:
        return token.lower() not in CONNECTORS and token.lower() not in LEGAL_FORMS

    found: set[str] = set()
    n = len(tokens)
    for i in range(n):
        for j in range(i + 2, n + 1):
            seq = tokens[i:j]
            if j - i == n:
                continue
            if seq[0].lower() in CONNECTORS or seq[-1].lower() in CONNECTORS:
                continue
            if not any(usable(t) for t in seq):
                continue
            found.add(" ".join(seq))
    if tokens[0][0].isalpha():
        found.add(f"{tokens[0][0]}. {' '.join(tokens[1:])}")
    for token in tokens[1:]:
        if len(token) >= 4 and usable(token) and token[0].isupper():
            found.add(token)
    return sorted(found)


def _key(text: str) -> str:
    return re.sub(r"\s+", "", fold(text))


def _pattern(text: str) -> str:
    parts: list[str] = []
    for token in text.split():
        if parts:
            parts.append(r"\s*" if parts[-1].endswith(r"\.") else r"\s+")
        parts.append(re.escape(fold(token)))
    return r"(?<!\w)" + "".join(parts) + r"(?!\w)"


class Matcher:
    """Encuentra todas las apariciones de una lista de términos.

    - Ignora mayúsculas y tildes ("PEREZ" encuentra "Pérez").
    - Las variantes derivadas solo se aceptan si empiezan en mayúscula, para que
      "Mayor" (de "Calle Mayor") no sustituya "mayor de edad".
    - Si una variante es común a dos términos con sustitutos distintos (dos
      personas apellidadas Pérez), no se aplica y se informa en `ambiguous`.
    """

    def __init__(self, terms: list[Term]):
        self.ambiguous: set[str] = set()
        entries: dict[str, tuple[Term, bool, str]] = {}
        derived: dict[str, list[tuple[Term, str]]] = {}

        for term in terms:
            if not term.original.strip():
                continue
            entries.setdefault(_key(term.original), (term, False, term.original))
        for term in terms:
            if not term.expand:
                continue
            for variant in variants(term.original):
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

    def find(self, text: str) -> list[Match]:
        if self._regex is None:
            return []
        matches = []
        for m in self._regex.finditer(fold(text)):
            entry = self._entries.get(_key(m.group()))
            if entry is None:
                continue
            term, strict_case, _ = entry
            if strict_case and not text[m.start()].isupper():
                continue
            matches.append(
                Match(m.start(), m.end(), text[m.start() : m.end()], term.replacement, term.source)
            )
        return matches

    def replace(self, text: str) -> str:
        for m in reversed(self.find(text)):
            text = text[: m.start] + m.replacement + text[m.end :]
        return text
