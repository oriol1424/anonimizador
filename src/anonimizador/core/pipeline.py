"""Flujo completo: analizar -> sugerir -> anonimizar -> verificar."""

import os
import re
import threading
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from anonimizador.core import docx_io, ner, pdf_io, regex_es
from anonimizador.core.guide import GuideEntry, build_entries, write_guide
from anonimizador.core.lang import DEFAULT_LANGUAGE, Language
from anonimizador.core.matcher import Matcher, Term
from anonimizador.core.progress import Progress, phase
from anonimizador.core.text import fold
from anonimizador.i18n import tr

# Formato de entrada -> (módulo que lo procesa, formatos de salida posibles).
FORMATS: dict[str, tuple[ModuleType, tuple[str, ...]]] = {
    ".docx": (docx_io, (".docx", ".txt")),
    ".pdf": (pdf_io, (".pdf", ".txt")),
}
SUPPORTED_INPUTS = set(FORMATS)


@dataclass(frozen=True)
class DocumentInfo:
    kind: str  # "docx" o "pdf"
    pages: int | None = None  # solo PDF (en Word depende de cómo se imprima)
    scanned: int = 0


def document_info(path: Path) -> DocumentInfo:
    """Qué es el documento, para mostrarlo al elegirlo (y avisar pronto si no se puede
    abrir: p. ej. un PDF protegido). Llamar ANTES de `read_ahead`: PyMuPDF no admite
    dos hilos a la vez."""
    _backend(path)
    if path.suffix.lower() != ".pdf":
        return DocumentInfo("docx")
    with _friendly_errors():
        pages, scanned = pdf_io.page_counts(path)
    return DocumentInfo("pdf", pages, scanned)


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
    expand: bool = False  # nombres: sustituir también variantes ("Sr. Casals")

    @property
    def text(self) -> str:
        return self.forms[0]

    def to_terms(self, replacement: str | None = None) -> list[Term]:
        alias = replacement or self.replacement
        return [Term(f, alias, expand=self.expand, source=self.label) for f in self.forms]


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
    """Aviso para el usuario: "ambiguous", "leftovers", "leftovers_scan", "images" u "ocr"."""

    kind: str
    detail: str = ""
    count: int = 0
    pages: str = ""  # páginas afectadas ("3, 12"), si se conocen

    @property
    def is_leak(self) -> bool:
        """Quedan datos sin borrar."""
        return self.kind in ("leftovers", "leftovers_scan")

    @property
    def is_serious(self) -> bool:
        """El aviso debe destacarse: datos sin borrar o páginas que no se han procesado."""
        return self.is_leak or self.kind in ("failed_pages", "unreadable_pages")

    def message(self, language: Language) -> str:
        return tr(
            language.code, f"notice_{self.kind}",
            detail=self.detail, count=self.count, pages=self.pages,
        )  # fmt: skip


@dataclass
class Analysis:
    suggestions: list[Suggestion]
    notices: list[Notice] = field(default_factory=list)


@dataclass
class Report:
    output: Path
    replaced: dict[str, int]  # sustituto -> nº de sustituciones
    notices: list[Notice] = field(default_factory=list)
    entries: list[GuideEntry] = field(default_factory=list)
    guide: Path | None = None

    @property
    def total(self) -> int:
        return sum(self.replaced.values())


class ReadAhead:
    """OCR anticipado de un PDF en un hilo aparte (ver `pdf_io.read_ahead`)."""

    def __init__(self, path: Path):
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=pdf_io.read_ahead, args=(path, self._stop), name="read-ahead", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Detiene la lectura; hay que llamarlo antes de analizar o anonimizar."""
        self._stop.set()
        self._thread.join()


def read_ahead(path: Path) -> ReadAhead | None:
    """Empieza a leer con OCR las páginas escaneadas en cuanto se elige el fichero."""
    return ReadAhead(path) if path.suffix.lower() == ".pdf" else None


def _pages(numbers) -> str:
    return ", ".join(map(str, sorted(set(numbers))))


def _doubts_notice(doubts: dict[int, int]) -> Notice:
    return Notice("ocr_doubtful", count=sum(doubts.values()), pages=_pages(doubts))


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


# Orden de las sugerencias en la ventana: primero lo más identificativo.
LABEL_ORDER = [
    "PERSONA", "EMPRESA", "DIRECCION", "PASAPORTE", "DNI", "NIE", "NRT", "CASS", "RESIDENCIA",
    "NACIMIENTO", "CIF", "TELEFONO", "EMAIL", "IBAN", "MATRICULA", "PROCEDIMIENTO",
]  # fmt: skip
NAMED_LABELS = {"PERSONA", "EMPRESA"}


def _overlaps(start: int, end: int, spans) -> bool:
    return any(start < s.end and end > s.start for s in spans)


def _same_file(a: Path, b: Path) -> bool:
    """Mismo fichero aunque cambie la ruta o las mayúsculas (en Windows y macOS
    "Demanda.docx" y "demanda.docx" son el mismo fichero)."""
    if a.resolve() == b.resolve():
        return True
    try:
        return a.exists() and os.path.samefile(a, b)
    except OSError:
        return False


def _part_of_user_term(text: str, user_terms: list[Term]) -> bool:
    """ "Joan" cuando el usuario ya puso "Joan Puig i Ferrer": es la misma persona."""
    words = set(fold(text).split())
    return any(words <= set(fold(t.original).split()) for t in user_terms)


def analyze(
    path: Path,
    user_terms: list[Term],
    language: Language = DEFAULT_LANGUAGE,
    progress: Progress | None = None,
) -> Analysis:
    """Busca datos identificativos que el usuario no ha incluido en su lista.

    Combina reglas (DNI, IBAN, direcciones...) y el detector de personas y empresas.
    El idioma decide el nombre de los alias sugeridos ([TELEFON_1] / [TELEFONO_1]).
    """
    backend = _backend(path)
    doubts: dict[int, int] = {}
    unreadable: set[int] = set()
    with _friendly_errors():
        if backend is pdf_io:
            text = pdf_io.extract_text(
                path, phase(progress, "read"), doubts=doubts, failed=unreadable
            )
        else:
            text = backend.extract_text(path)
    # Lo que el usuario ya puso en su lista y lo que no se anonimiza nunca (la abogada,
    # el despacho): no se sugiere.
    matcher = Matcher(user_terms)
    covered = matcher.find(text, include_kept=True)
    user_terms = [t for t in user_terms if not t.keep]

    rules = [d for d in regex_es.detect(text) if not _overlaps(d.start, d.end, covered)]
    entities = [
        e
        for e in ner.detect(text, phase(progress, "detect"))
        if not _overlaps(e.start, e.end, covered)
        and not _overlaps(e.start, e.end, rules)
        and not _part_of_user_term(e.text, user_terms)
    ]

    groups: dict[tuple[str, str], list[str]] = {}
    first_seen: dict[tuple[str, str], int] = {}
    for label, key, form, start in [
        *((d.label, _normalize_value(d.text), d.text, d.start) for d in rules),
        *((e.label, fold(e.text), e.text, e.start) for e in entities),
    ]:
        groups.setdefault((label, key), []).append(form)
        first_seen[(label, key)] = min(first_seen.get((label, key), start), start)

    ordered = sorted(groups, key=lambda k: (LABEL_ORDER.index(k[0]), first_seen[k]))
    raw = [
        Suggestion(
            label, "", tuple(dict.fromkeys(groups[(label, key)])), len(groups[(label, key)]),
            expand=label in NAMED_LABELS,
        )
        for label, key in ordered
    ]  # fmt: skip
    merged = merge_variants(raw)
    merged.sort(key=lambda s: LABEL_ORDER.index(s.label))
    used = {t.replacement for t in user_terms}
    suggestions = [
        Suggestion(s.label, _next_alias(language.labels[s.label], used), s.forms, s.count,
                   s.expand)
        for s in merged
    ]  # fmt: skip

    notices = [Notice("ambiguous", detail=v) for v in sorted(matcher.ambiguous)]
    if unreadable:
        notices.append(Notice("unreadable_pages", count=len(unreadable), pages=_pages(unreadable)))
    if doubts:
        notices.append(_doubts_notice(doubts))
    if not ner.is_available():
        notices.append(Notice("ner_unavailable"))
    return Analysis(suggestions, notices)


def merge_variants(suggestions: list[Suggestion]) -> list[Suggestion]:
    """Junta en una sola sugerencia las formas de un mismo nombre.

    "Jordi Casals i Pons", "Sr. Casals" y "J. Casals Pons" -> una sugerencia con las tres
    formas. Sin IA: se usan las mismas variantes con las que se sustituye.
    """
    named = sorted((s for s in suggestions if s.expand), key=lambda s: len(s.text), reverse=True)
    merged: dict[int, Suggestion] = {}
    _origin: dict[Suggestion, Suggestion] = {}
    absorbed: set[int] = set()
    for i, longer in enumerate(named):
        if i in absorbed:
            continue
        matcher = Matcher([Term(longer.text, "x")])
        forms, count = list(longer.forms), longer.count
        for j in range(i + 1, len(named)):
            shorter = named[j]
            if j in absorbed:
                continue
            found = matcher.find(shorter.text)
            if found and found[0].start == 0 and found[0].end == len(shorter.text):
                forms += [f for f in shorter.forms if f not in forms]
                count += shorter.count
                absorbed.add(j)
        result = Suggestion(longer.label, longer.replacement, tuple(forms), count, True)
        merged[i] = result
        _origin[result] = longer
    position = {id(s): n for n, s in enumerate(suggestions)}
    kept = sorted(merged.values(), key=lambda s: position.get(id(_origin[s]), 0))
    return [s for s in suggestions if not s.expand] + kept


def anonymize(
    src: Path,
    dst: Path,
    terms: list[Term],
    progress: Progress | None = None,
    guide: Path | None = None,
    language: Language = DEFAULT_LANGUAGE,
) -> Report:
    """Anonimiza y verifica releyendo la salida (en páginas escaneadas, con un nuevo OCR).

    Si se indica `guide`, guarda ahí la guía de correspondencias (alias -> texto original).
    """
    backend = _backend(src)
    native = src.suffix.lower()
    if dst.suffix.lower() not in output_formats(src):
        raise AnonymizerError("unsupported_output", suffix=dst.suffix)
    if any(_same_file(path, src) for path in (dst, guide) if path is not None):
        raise AnonymizerError("same_file")

    matcher = Matcher(terms)
    work = dst if dst.suffix.lower() == native else dst.with_suffix(".tmp" + native)
    try:
        with _friendly_errors():
            failed: set[int] = set()
            if backend is pdf_io:
                result = pdf_io.anonymize(
                    src, work, matcher, phase(progress, "anonymize"), language.failed_page
                )
                failed |= result.failed_pages
            else:
                result = backend.anonymize(src, work, matcher)
            if backend is pdf_io:
                # Las páginas imagen ya se verificaron con OCR al anonimizarlas: aquí se
                # revisa su capa de texto y el resto del documento.
                leftovers = matcher.find(
                    pdf_io.extract_text(work, phase(progress, "verify"), use_ocr=False)
                )
            else:
                leftovers = matcher.find(backend.extract_text(work))
            if work != dst:
                text = (
                    pdf_io.anonymized_text(
                        src, matcher, phase(progress, "export"), language.failed_page, failed
                    )
                    if backend is pdf_io
                    else docx_io.body_text(work)
                )
                dst.write_text(text, encoding="utf-8")
    except BaseException:
        # Sin salida a medias o sin verificar: o se termina entero, o no queda nada.
        dst.unlink(missing_ok=True)
        raise
    finally:
        if work != dst:
            work.unlink(missing_ok=True)

    notices: list[Notice] = []
    if failed:
        notices.append(Notice("failed_pages", count=len(failed), pages=_pages(failed)))
    if result.scan_leftovers:
        notices.append(
            Notice(
                "leftovers_scan",
                detail=", ".join(sorted({m.text for _, m in result.scan_leftovers})),
                count=len(result.scan_leftovers),
                pages=_pages(page for page, _ in result.scan_leftovers),
            )
        )
    if result.ocr_doubts:
        notices.append(_doubts_notice(result.ocr_doubts))
    if result.scanned_pages:
        notices.append(Notice("ocr", count=result.scanned_pages))
    if leftovers:
        detail = ", ".join(sorted({m.text for m in leftovers}))
        notices.append(Notice("leftovers", detail=detail, count=len(leftovers)))
    if result.images:
        notices.append(Notice("images", count=result.images))
    if result.attachments_removed:
        notices.append(Notice("attachments_removed", count=result.attachments_removed))

    replaced = Counter(m.replacement for m in result.matches)
    entries = build_entries([t for t in terms if not t.keep], result.matches)
    if guide is not None:
        write_guide(guide, entries, src, dst, language)
    return Report(dst, dict(replaced), notices, entries, guide)
