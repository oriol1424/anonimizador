"""Flujo completo: analizar -> sugerir -> anonimizar -> verificar."""

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from anonimizador.core import docx_io, regex_es
from anonimizador.core.lang import DEFAULT_LANGUAGE, Language
from anonimizador.core.matcher import Matcher, Term
from anonimizador.i18n import tr

SUPPORTED_INPUTS = {".docx"}
SUPPORTED_OUTPUTS = {".docx", ".txt"}


@dataclass(frozen=True)
class Suggestion:
    """Algo que el usuario no indicó y parece un dato identificativo."""

    label: str
    replacement: str
    forms: tuple[str, ...]  # cómo aparece en el texto ("12345678Z", "12.345.678-Z")
    count: int

    @property
    def text(self) -> str:
        return self.forms[0]

    def to_terms(self, replacement: str | None = None) -> list[Term]:
        alias = replacement or self.replacement
        return [Term(f, alias, expand=False, source=self.label) for f in self.forms]


class AnonymizerError(ValueError):
    """Error explicable al usuario. `kind` es la clave de traducción (sin "error_")."""

    def __init__(self, kind: str, **params: object):
        self.kind = kind
        self.params = params
        super().__init__(tr(DEFAULT_LANGUAGE.code, f"error_{kind}", **params))

    def message(self, language: Language) -> str:
        return tr(language.code, f"error_{self.kind}", **self.params)


@dataclass(frozen=True)
class Notice:
    """Aviso para el usuario: "ambiguous", "leftovers" o "images"."""

    kind: str
    detail: str = ""
    count: int = 0

    def message(self, language: Language) -> str:
        return tr(language.code, f"notice_{self.kind}", detail=self.detail, count=self.count)


@dataclass
class Analysis:
    suggestions: list[Suggestion]
    notices: list[Notice] = field(default_factory=list)


@dataclass
class Report:
    output: Path
    replaced: dict[str, int]  # sustituto -> nº de sustituciones
    notices: list[Notice] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(self.replaced.values())


def _check_input(path: Path) -> None:
    if path.suffix.lower() not in SUPPORTED_INPUTS:
        raise AnonymizerError("unsupported_input", suffix=path.suffix)


def _normalize_value(text: str) -> str:
    return re.sub(r"[\s.\-]", "", text.upper())


def _next_alias(label: str, used: set[str]) -> str:
    n = 1
    while f"[{label}_{n}]" in used:
        n += 1
    alias = f"[{label}_{n}]"
    used.add(alias)
    return alias


def analyze(path: Path, user_terms: list[Term], language: Language = DEFAULT_LANGUAGE) -> Analysis:
    """Busca datos identificativos que el usuario no ha incluido en su lista.

    El idioma decide el nombre de los alias sugeridos ([TELEFON_1] / [TELEFONO_1]) y, más
    adelante, el modelo de detección de nombres.
    """
    _check_input(path)
    text = docx_io.extract_text(path)
    matcher = Matcher(user_terms)
    covered = matcher.find(text)

    groups: dict[tuple[str, str], list[str]] = {}
    for det in regex_es.detect(text):
        if any(det.start < c.end and det.end > c.start for c in covered):
            continue
        groups.setdefault((det.label, _normalize_value(det.text)), []).append(det.text)

    used = {t.replacement for t in user_terms}
    suggestions = [
        Suggestion(
            label,
            _next_alias(language.labels[label], used),
            tuple(dict.fromkeys(forms)),
            len(forms),
        )
        for (label, _), forms in groups.items()
    ]
    notices = [Notice("ambiguous", detail=v) for v in sorted(matcher.ambiguous)]
    return Analysis(suggestions, notices)


def anonymize(src: Path, dst: Path, terms: list[Term]) -> Report:
    _check_input(src)
    if dst.suffix.lower() not in SUPPORTED_OUTPUTS:
        raise AnonymizerError("unsupported_output", suffix=dst.suffix)
    if dst.resolve() == src.resolve():
        raise AnonymizerError("same_file")

    matcher = Matcher(terms)
    docx_dst = dst if dst.suffix.lower() == ".docx" else dst.with_suffix(".tmp.docx")
    result = docx_io.anonymize_docx(src, docx_dst, matcher)

    notices: list[Notice] = []
    leftovers = matcher.find(docx_io.extract_text(docx_dst))
    if leftovers:
        detail = ", ".join(sorted({m.text for m in leftovers}))
        notices.append(Notice("leftovers", detail=detail, count=len(leftovers)))
    if result.images:
        notices.append(Notice("images", count=result.images))

    if docx_dst != dst:
        dst.write_text(docx_io.body_text(docx_dst), encoding="utf-8")
        docx_dst.unlink()

    replaced = Counter(m.replacement for m in result.matches)
    return Report(dst, dict(replaced), notices)
