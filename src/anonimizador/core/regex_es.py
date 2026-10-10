"""Detección por reglas de datos identificativos españoles."""

import re
from dataclasses import dataclass
from typing import Protocol, TypeVar


@dataclass(frozen=True)
class Detection:
    start: int
    end: int
    text: str
    label: str


def _iban_valid(raw: str) -> bool:
    iban = re.sub(r"\s", "", raw).upper()
    digits = "".join(str(int(c, 36)) for c in iban[4:] + iban[:4])
    return int(digits) % 97 == 1


# --- Direcciones postales (catalán y castellano) ----------------------------------------
# "carrer de la Indústria, 45, 3r 2a, 08025 Barcelona", "Av. Diagonal 640", "C/ Major, s/n",
# "carretera de Sant Sadurní, km 3, de Vilafranca del Penedès", "calle Mayor 5, 2º B".
_STREET = (
    r"carrer|c/|avinguda|avgda\.|avda\.|av\.|passeig|pg\.|passatge|ptge\.|plaça|pça\.|pl\.|"
    r"carretera|ctra\.|ronda|travessera|travessia|rambla|camí|via|baixada|pujada|"
    r"urbanització|urb\.|polígon|pol\.|calle|c\.|avenida|paseo|pº|plaza|pza\.|camino|travesía"
)
_UPPER = "A-ZÀ-ÖØ-ÞÇÑ"
_PARTICLES = r"(?:(?:de\s+la|de\s+les|de\s+los|de|del|dels|d'|d’|l'|l’|la|les|el|els|en|na|sa)\s*)*"
# Nombre de la vía: sin cifras ni final de frase (". Que..."), salvo abreviaturas habituales.
_ABBR = r"(?:Dr|Dra|St|Sta|Mn|Gral|Pare|Sr|Sra)\.\s"
_NAME_CHAR = rf"(?:{_ABBR}|(?!\.\s)[^\d\n;:()])"
_NUMBER = r"(?:,?\s*(?:(?:n[úu]m\.?|nº|n\.º)\s*)?\d{1,4}(?:-\d{1,4})?(?:\s?bis)?|,?\s*s/n)"
_FLOOR = (
    r"(?:,?\s*(?:\d{1,2}\s?[ºª]\s?[A-Z]\b"
    r"|\d{1,2}\s?(?:r|n|t|è|º|ª|o|a)\.?(?:\s*\d{1,2}\s?(?:a|ª|º|o)\.?)?|baixos|bxs\.?|principal|pral\.?|àtic|entresòl|entl\.?"
    r"|bajo|ático|entresuelo|(?:escala|esc\.)\s*\w|(?:porta|pta\.)\s*\d+))*"
)
_CITY = rf"[{_UPPER}][\w'’·-]+(?:\s+(?:(?:de|del|la|les|i|d'|d’)\s*)?[{_UPPER}][\w'’·-]+){{0,3}}"
ADDRESS = re.compile(
    rf"(?<!\w)(?i:{_STREET})(?:(?<=[./])|\b)\s*{_PARTICLES}(?:{_ABBR}|[{_UPPER}]){_NAME_CHAR}{{0,60}}?"
    rf"{_NUMBER}{_FLOOR}(?:,?\s*\d{{5}})?(?:,?\s*(?:de\s+|d'|d’)?{_CITY})?"
)


# El orden importa: ante solapes gana la detección más larga y, a igualdad, la primera.
RULES: list[tuple[str, re.Pattern[str], object]] = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), None),
    (
        "IBAN",
        re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,4})?\b"),
        _iban_valid,
    ),
    ("DNI", re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}[- ]?[A-Z]\b"), None),
    ("NIE", re.compile(r"\b[XYZ][- ]?\d{7}[- ]?[A-Z]\b"), None),
    ("CIF", re.compile(r"\b[ABCDEFGHJNPQRSUVW][- ]?\d{7}[- ]?[0-9A-J]\b"), None),
    ("TELEFONO", re.compile(r"(?<![\w+])(?:(?:\+|00)34[ .-]?)?[6789](?:[ .-]?\d){8}(?!\d)"), None),
    ("MATRICULA", re.compile(r"\b\d{4}[- ]?[BCDFGHJKLMNPRSTVWXYZ]{3}\b"), None),
    ("PROCEDIMIENTO", re.compile(r"\b\d{1,6}/(?:19|20)\d{2}\b"), None),
    ("DIRECCION", ADDRESS, None),
]


def detect(text: str) -> list[Detection]:
    found: list[Detection] = []
    for label, regex, validator in RULES:
        for m in regex.finditer(text):
            if validator is not None and not validator(m.group()):
                continue
            found.append(Detection(m.start(), m.end(), m.group(), label))
    return remove_overlaps(found)


class _Span(Protocol):
    start: int
    end: int


S = TypeVar("S", bound=_Span)


def remove_overlaps(items: list[S]) -> list[S]:
    """Se queda con las detecciones más largas cuando se solapan."""
    chosen: list[S] = []
    for item in sorted(items, key=lambda d: (-(d.end - d.start), d.start)):
        if all(item.end <= c.start or item.start >= c.end for c in chosen):
            chosen.append(item)
    return sorted(chosen, key=lambda d: d.start)
