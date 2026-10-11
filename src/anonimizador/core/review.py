"""Revisión final: palabras con mayúscula que siguen en el documento anonimizado.

Sin IA: es la red de seguridad contra lo que el detector no vio. Se descartan los
inicios de frase, los alias ([CLIENT_1]) y palabras habituales en los escritos (Batllia,
Article, meses...). Lo que queda se resalta para que el abogado lo repase en segundos.
"""

import re
from collections import Counter
from pathlib import Path

from anonimizador.core import docx_io, pdf_io
from anonimizador.core.text import fold

_UPPER = "A-ZÀ-ÖØ-ÞÇÑ"
WORD = re.compile(rf"(?<![\w·'’\[])[{_UPPER}][\w·'’-]*\w")
ALIAS = re.compile(r"\[[A-Z0-9_]+\]")
SENTENCE_END = set('.!?:;«"“(—-–•\n')

# Palabras que suelen ir en mayúscula en los escritos y no identifican a nadie (ca/es).
COMMON = {
    # tratamientos y fórmulas
    "sr", "sra", "srta", "senyor", "senyora", "señor", "señora", "don", "dona", "doña",
    "il·lustre", "ilustre", "excm", "excma", "excmo", "honorable", "lletrat",
    "lletrada", "letrado", "letrada", "advocat", "advocada", "procurador", "procuradora",
    # órganos y normas
    "batllia", "batlle", "tribunal", "superior", "corts", "justicia", "justícia", "jutjat",
    "juzgado", "sala", "secció", "sección", "fiscalia", "ministeri", "ministerio", "govern",
    "gobierno", "consell", "consejo", "general", "comú", "comuns", "principat", "andorra",
    "andorrà", "andorrana", "espanya", "españa", "estat", "estado", "llei", "ley",
    "qualificada", "decret", "decreto", "reglament", "reglamento", "codi", "código",
    "civil", "penal", "procesal", "processal", "constitució", "constitución", "article",
    "artículo", "disposició", "disposición", "addicional", "transitòria", "transitoria",
    "final", "derogatòria", "butlletí", "boletín", "oficial", "bopa", "boe", "cass", "caixa",
    "seguretat", "social", "seguridad", "registre", "registro", "mercantil", "propietat",
    "propiedad", "notari", "notario", "policia", "policía", "cos", "raonador",
    # partes del escrito
    "demanda", "contestació", "contestación", "recurs", "recurso", "apel·lació",
    "apelación", "sentència", "sentencia", "interlocutòria", "auto", "providència",
    "providencia", "diligència", "diligencia", "fets", "hechos", "fonaments", "fundamentos",
    "dret", "derecho", "suplico", "supliquem", "diu", "dice", "exposa", "expone",
    "sol·licita", "solicita", "primer", "primera", "segon", "segona", "segundo", "tercer",
    "tercera", "quart", "quarta", "cuarto", "cinquè", "quinto", "sisè", "sexto", "annex",
    "anexo", "document", "documento", "otrosí", "altresí", "part", "parte", "actora",
    "demandant", "demandat", "demandada", "demandante", "demandado", "testimoni", "testigo",
    "perit", "perito", "euros", "euro", "eur", "iva", "nif", "nie", "dni", "nrt", "iban",
    "sl", "sa", "slu", "sau",
    # fechas
    "gener", "febrer", "març", "abril", "maig", "juny", "juliol", "agost", "setembre",
    "octubre", "novembre", "desembre", "enero", "febrero", "marzo", "mayo", "junio", "julio",
    "agosto", "septiembre", "noviembre", "diciembre", "dilluns", "dimarts", "dimecres",
    "dijous", "divendres", "dissabte", "diumenge", "lunes", "martes", "miércoles", "jueves",
    "viernes", "sábado", "domingo",
}  # fmt: skip


_COMMON = frozenset(fold(w) for w in COMMON)
# Abreviaturas con punto que no terminan la frase.
_ABBREVIATIONS = frozenset(fold(a) for a in (
    "sr", "sra", "srta", "dr", "dra", "mn", "st", "sta", "núm", "art", "av", "avda", "c",
    "pg", "pl", "ctra", "d", "dª", "excm", "excma",
))  # fmt: skip


def _sentence_start(text: str, start: int) -> bool:
    i = start - 1
    while i >= 0 and text[i] in " 	 ":
        i -= 1
    if i < 0:
        return True
    if text[i] == ".":
        before = re.search(r"([\w·ª]+)\.$", text[max(0, i - 8) : i + 1])
        if before and fold(before.group(1)) in _ABBREVIATIONS:
            return False  # "el Sr. Casals": el punto no termina la frase
    return text[i] in SENTENCE_END


def suspicious(text: str, ignore: set[str] = frozenset()) -> list[tuple[str, int]]:
    """(palabra, veces) a revisar, las más repetidas primero.

    `ignore`: textos que no se deben señalar (p. ej. la lista «No anonimitzar»).
    """
    clean = ALIAS.sub(lambda m: " " * len(m.group()), text)
    ignored = {fold(w) for item in ignore for w in item.split()}
    counts: Counter[str] = Counter()
    for m in WORD.finditer(clean):
        word = m.group()
        key = fold(word).strip("'’")
        if len(word) < 3 or key in _COMMON or key in ignored or _sentence_start(clean, m.start()):
            continue
        counts[word] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], fold(item[0])))


def review_text(path: Path) -> str:
    """Texto del documento ya anonimizado tal como lo leería la IA (sin OCR: rápido)."""
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".docx":
        return docx_io.visible_text(path)
    return pdf_io.extract_text(path, use_ocr=False)
