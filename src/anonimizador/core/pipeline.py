"""Flujo completo: analizar -> sugerir -> anonimizar -> verificar."""

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from anonimizador.core import docx_io, regex_es
from anonimizador.core.matcher import Matcher, Term

SUPPORTED_INPUTS = {".docx"}
SUPPORTED_OUTPUTS = {".docx", ".txt"}

# Opciones del desplegable "Sustituir por" (la interfaz permite además escribir cualquier texto).
REPLACEMENT_PRESETS = [
    "[PERSONA_{n}]",
    "[CLIENTE_{n}]",
    "[CONTRARIO_{n}]",
    "[EMPRESA_{n}]",
    "[DIRECCION_{n}]",
    "Persona {letra}",
    "***",
]


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


@dataclass
class Analysis:
    suggestions: list[Suggestion]
    warnings: list[str] = field(default_factory=list)


@dataclass
class Report:
    output: Path
    replaced: dict[str, int]  # sustituto -> nº de sustituciones
    warnings: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(self.replaced.values())


def _check_input(path: Path) -> None:
    if path.suffix.lower() not in SUPPORTED_INPUTS:
        raise ValueError(f"Formato no soportado todavía: {path.suffix}")


def _normalize_value(text: str) -> str:
    return re.sub(r"[\s.\-]", "", text.upper())


def _next_alias(label: str, used: set[str]) -> str:
    n = 1
    while f"[{label}_{n}]" in used:
        n += 1
    alias = f"[{label}_{n}]"
    used.add(alias)
    return alias


def analyze(path: Path, user_terms: list[Term]) -> Analysis:
    """Busca datos identificativos que el usuario no ha incluido en su lista."""
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
        Suggestion(label, _next_alias(label, used), tuple(dict.fromkeys(forms)), len(forms))
        for (label, _), forms in groups.items()
    ]
    warnings = [
        f'"{v}" coincide con varios términos con sustitutos distintos; no se ha sustituido '
        "automáticamente. Revísalo y añádelo a la lista con el sustituto correcto."
        for v in sorted(matcher.ambiguous)
    ]
    return Analysis(suggestions, warnings)


def anonymize(src: Path, dst: Path, terms: list[Term]) -> Report:
    _check_input(src)
    if dst.suffix.lower() not in SUPPORTED_OUTPUTS:
        raise ValueError(f"Formato de salida no soportado: {dst.suffix}")
    if dst.resolve() == src.resolve():
        raise ValueError("El fichero de salida no puede ser el mismo que el original.")

    matcher = Matcher(terms)
    docx_dst = dst if dst.suffix.lower() == ".docx" else dst.with_suffix(".tmp.docx")
    result = docx_io.anonymize_docx(src, docx_dst, matcher)

    warnings: list[str] = []
    leftovers = matcher.find(docx_io.extract_text(docx_dst))
    if leftovers:
        warnings.append(
            f"Verificación: quedan {len(leftovers)} apariciones sin sustituir "
            f"({', '.join(sorted({m.text for m in leftovers}))}). Revisa el documento."
        )
    if result.images:
        warnings.append(
            f"El documento contiene {result.images} imágenes u objetos incrustados. "
            "Su contenido no se anonimiza: revísalos manualmente."
        )

    if docx_dst != dst:
        dst.write_text(docx_io.body_text(docx_dst), encoding="utf-8")
        docx_dst.unlink()

    replaced = Counter(m.replacement for m in result.matches)
    return Report(dst, dict(replaced), warnings)
