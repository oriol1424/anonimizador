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
