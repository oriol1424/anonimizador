"""Flujo completo: analizar -> sugerir -> anonimizar -> verificar."""

import re
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from anonimizador.core import docx_io, pdf_io, regex_es
from anonimizador.core.lang import DEFAULT_LANGUAGE, Language
from anonimizador.core.matcher import Matcher, Term
from anonimizador.i18n import tr

# Formato de entrada -> (módulo que lo procesa, formatos de salida posibles).
FORMATS: dict[str, tuple[ModuleType, tuple[str, ...]]] = {
    ".docx": (docx_io, (".docx", ".txt")),
    ".pdf": (pdf_io, (".pdf", ".txt")),
}
SUPPORTED_INPUTS = set(FORMATS)


def output_formats(path: Path) -> tuple[str, ...]:
    """Formatos en los que se puede guardar un documento de entrada."""
    return FORMATS.get(path.suffix.lower(), (None, ()))[1]


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
    """Aviso para el usuario: "ambiguous", "leftovers", "images" o "scanned"."""

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


def _backend(path: Path) -> ModuleType:
    if path.suffix.lower() not in FORMATS:
        raise AnonymizerError("unsupported_input", suffix=path.suffix)
    return FORMATS[path.suffix.lower()][0]


@contextmanager
def _friendly_errors():
    """Traduce errores conocidos de los formatos a mensajes para el usuario."""
    try:
        yield
    except pdf_io.EncryptedPdfError:
        raise AnonymizerError("encrypted") from None


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
    backend = _backend(path)
    with _friendly_errors():
        text = backend.extract_text(path)
        scanned = pdf_io.scanned_pages(path) if backend is pdf_io else 0
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
    if scanned:
        notices.insert(0, Notice("scanned", count=scanned))
    return Analysis(suggestions, notices)


def anonymize(src: Path, dst: Path, terms: list[Term]) -> Report:
    backend = _backend(src)
    native = src.suffix.lower()
    if dst.suffix.lower() not in output_formats(src):
        raise AnonymizerError("unsupported_output", suffix=dst.suffix)
    if dst.resolve() == src.resolve():
        raise AnonymizerError("same_file")

    matcher = Matcher(terms)
    work = dst if dst.suffix.lower() == native else dst.with_suffix(".tmp" + native)
    try:
        with _friendly_errors():
            result = backend.anonymize(src, work, matcher)
            leftovers = matcher.find(backend.extract_text(work))
            if work != dst:
                text = (
                    pdf_io.anonymized_text(src, matcher)
                    if backend is pdf_io
                    else docx_io.body_text(work)
                )
                dst.write_text(text, encoding="utf-8")
    finally:
        if work != dst:
            work.unlink(missing_ok=True)

    notices: list[Notice] = []
    if result.scanned_pages:
        notices.append(Notice("scanned", count=result.scanned_pages))
    if leftovers:
        detail = ", ".join(sorted({m.text for m in leftovers}))
        notices.append(Notice("leftovers", detail=detail, count=len(leftovers)))
    if result.images:
        notices.append(Notice("images", count=result.images))

    replaced = Counter(m.replacement for m in result.matches)
    return Report(dst, dict(replaced), notices)
