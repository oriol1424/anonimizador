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
    rf"{_NUMBER}{_FLOOR}(?:,?\s*(?:\d{{5}}|AD[- ]?\d{{3}}))?(?:,?\s*(?:de\s+|d'|d’)?{_CITY})?"
)

# Pasaportes de cualquier país: el número que sigue a la palabra "passaport", "pasaporte",
# "passeport" o "passport". Solo se marca el número (grupo "v"), no la palabra.
PASSPORT = re.compile(
    r"(?i:passaports?|pasaportes?|passeports?|passports?)"
    r"(?:\s+(?i:n[úu]m(?:ero|\.)?|n\.?º|no\.?|nr\.?|number))?\s*:?\s*"
    r"(?P<v>(?=[A-Z]*\d)[A-Z0-9]{6,9})\b"
)
# Andorra: 6 cifras (fijos 7/8, móviles 3/6). Sin prefijo no se aceptan puntos:
# "600.000" es un importe, no un teléfono.
PHONE_AD = re.compile(
    r"(?<![\w+.,])(?:(?:\+|00)376[ .-]?[3678]\d{2}[ .-]?\d{3}|[3678]\d{2} ?\d{3})(?![.,]?\d)"
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
    # Andorra: NRT (letra + 6 cifras + letra de control, "F-123456-X") y pasaporte
    # andorrano ("O" + 7 cifras).
    ("NRT", re.compile(r"\b[A-Z][- ]?\d{6}[- ]?[A-Z]\b"), None),
    ("PASAPORTE", re.compile(r"\bO\d{7}\b"), None),
    ("PASAPORTE", PASSPORT, None),
    ("TELEFONO", re.compile(r"(?<![\w+])(?:(?:\+|00)34[ .-]?)?[6789](?:[ .-]?\d){8}(?!\d)"), None),
    ("TELEFONO", PHONE_AD, None),
    ("MATRICULA", re.compile(r"\b\d{4}[- ]?[BCDFGHJKLMNPRSTVWXYZ]{3}\b"), None),
    ("MATRICULA", re.compile(r"\b(?:AND|[A-Z])[- ]?\d{4}\b"), None),  # Andorra: "A 1234"
    ("PROCEDIMIENTO", re.compile(r"\b\d{1,6}/(?:19|20)\d{2}\b"), None),
    ("DIRECCION", ADDRESS, None),
]


def detect(text: str) -> list[Detection]:
    found: list[Detection] = []
    for label, regex, validator in RULES:
        group = "v" if "v" in regex.groupindex else 0
        for m in regex.finditer(text):
            if validator is not None and not validator(m.group(group)):
                continue
            found.append(Detection(m.start(group), m.end(group), m.group(group), label))
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
