"""Detección de personas y empresas con un modelo local (sin internet, sin PyTorch).

Modelo: projecte-aina/roberta-base-ca-v2-cased-ner (Projecte AINA / BSC, Apache-2.0),
convertido a ONNX y cuantizado a int8 con `scripts/preparar_models.py`. Se ejecuta con
onnxruntime + tokenizers. El modelo NO está en git: vive en `models/ner-ca/`.

En la evaluación (tests/corpus/ner_eval_ca.py) encontró 32/32 personas y empresas; las
direcciones las detectan las reglas de `regex_es.py` (7/7).
"""

import json
import os
import re
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

from anonimizador.core.text import fold

MODEL_NAME = "ner-ca"
CHUNK_CHARS = 1500  # ~400 tokens: por debajo del máximo del modelo (512)
MAX_TOKENS = 510
STRIDE = 64

# Tipos del modelo -> tipos de la app. LOC (ciudades sueltas) y MISC no se sugieren:
# las direcciones completas las detectan las reglas.
LABELS = {"PER": "PERSONA", "ORG": "EMPRESA"}

HONORIFICS = {
    "sr", "sra", "srta", "en", "na", "n'", "don", "dona", "doña", "senyor", "senyora",
    "señor", "señora", "dr", "dra", "lletrat", "lletrada", "letrado", "letrada",
}  # fmt: skip

# Organismos públicos: no son datos personales y aparecen en todos los escritos.
PUBLIC_BODIES = (
    "jutjat", "juzgado", "tribunal", "audiència", "audiencia", "sala ", "secció", "sección",
    "agència tributària", "agencia tributaria", "agència", "agencia estatal", "tresoreria",
    "tesorería", "seguretat social", "seguridad social", "inss", "sepe", "registre",
    "registro", "ajuntament", "ayuntamiento", "generalitat", "govern", "gobierno",
    "ministeri", "ministerio", "fiscalia", "fiscalía", "col·legi", "colegio", "icab",
    "mossos", "policia", "policía", "guàrdia civil", "guardia civil", "diputació",
    "diputación", "consell", "consejo", "parlament", "departament", "servei català",
    "institut català", "síndic", "defensor del", "hisenda", "hacienda", "boe", "dogc",
    "unió europea", "unión europea", "estat espanyol", "estado español",
    # Andorra. Se compara el inicio sin acentos: nada de prefijos cortos como "comú" o
    # "cass", que descartarían empresas como "Comunicacions Andorra SL" o "Cassany SL".
    "batllia", "comú d", "caixa andorrana de seguretat social", "butlletí oficial del",
    "principat d'andorra", "cos de policia", "raonador del ciutadà",
)  # fmt: skip


# Papeles procesales: en tablas y encabezados aparecen solos y el modelo los toma por nombres.
LEGAL_ROLES = {
    "demandant", "demandat", "demandada", "demandants", "demandats", "actor", "actora",
    "part actora", "part demandada", "demandante", "demandado", "parte actora",
    "parte demandada", "testimoni", "testigo", "perit", "perito", "procurador",
    "procuradora", "advocat", "advocada", "abogado", "abogada", "jutge", "jutgessa",
    "juez", "jueza", "fiscal", "recurrent", "recurrente", "apel·lant", "apelante",
    "apel·lat", "apelado", "querellant", "querellante", "querellat", "querellado",
    "denunciant", "denunciante", "denunciat", "denunciado", "arrendador", "arrendatari",
    "arrendatario", "fets", "hechos", "fonaments", "fundamentos", "suplico", "supliquem",
}  # fmt: skip
ELISIONS = {"d'", "l'"}
_APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'"})


@dataclass(frozen=True)
class Entity:
    start: int
    end: int
    text: str
    label: str  # "PERSONA" o "EMPRESA"


def models_dir() -> Path:
    """Carpeta de modelos: variable de entorno, junto al ejecutable o en el proyecto."""
    candidates = []
    if os.environ.get("ANONIMITZADOR_MODELS"):
        candidates.append(Path(os.environ["ANONIMITZADOR_MODELS"]))
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).parent / "models")
        candidates.append(Path(getattr(sys, "_MEIPASS", "")) / "models")
    candidates.append(Path(__file__).resolve().parents[3] / "models")
    for candidate in candidates:
        if (candidate / MODEL_NAME / "model.onnx").exists():
            return candidate
    return candidates[-1]


def is_available() -> bool:
    return (models_dir() / MODEL_NAME / "model.onnx").exists()


class _Model:
    def __init__(self, folder: Path):
        import onnxruntime
        from tokenizers import Tokenizer

        self.session = onnxruntime.InferenceSession(
            str(folder / "model.onnx"), providers=["CPUExecutionProvider"]
        )
        self.inputs = {i.name for i in self.session.get_inputs()}
        self.tokenizer = Tokenizer.from_file(str(folder / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=MAX_TOKENS, stride=STRIDE)
        config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
        self.id2label = {int(k): v for k, v in config["id2label"].items()}

    def _encodings(self, text: str):
        first = self.tokenizer.encode(text)
        return [first, *first.overflowing]

    def predict(self, text: str) -> list[tuple[int, int, str]]:
        """Entidades (inicio, fin, tipo del modelo) en un fragmento de texto."""
        import numpy as np

        spans: set[tuple[int, int, str]] = set()
        for enc in self._encodings(text):
            feed = {"input_ids": np.array([enc.ids], dtype=np.int64)}
            if "attention_mask" in self.inputs:
                feed["attention_mask"] = np.array([enc.attention_mask], dtype=np.int64)
            logits = self.session.run(None, feed)[0][0]
            labels = logits.argmax(-1)
            spans.update(self._decode(enc, labels))
        return sorted(spans)

    def _decode(self, enc, labels) -> list[tuple[int, int, str]]:
        # Etiqueta por palabra = la de su primer sub-token; luego esquema BIO por palabras.
        words: list[tuple[int, int, str]] = []
        last_word = None
        for word_id, (start, end), label_id in zip(enc.word_ids, enc.offsets, labels, strict=True):
            if word_id is None or start == end:
                continue
            if word_id == last_word:
                words[-1] = (words[-1][0], end, words[-1][2])
            else:
                words.append((start, end, self.id2label[int(label_id)]))
                last_word = word_id
        spans, current = [], None
        for start, end, tag in words:
            kind = tag[2:] if tag != "O" else None
            if kind and (tag.startswith("I-") and current and current[2] == kind):
                current = (current[0], end, kind)
                continue
            if current:
                spans.append(current)
            current = (start, end, kind) if kind else None
        if current:
            spans.append(current)
        return spans


_model: _Model | None = None
_lock = threading.Lock()


def _get_model() -> _Model:
    global _model
    with _lock:
        if _model is None:
            _model = _Model(models_dir() / MODEL_NAME)
        return _model


def _chunks(text: str) -> list[tuple[int, str]]:
    """Trozos de ~CHUNK_CHARS caracteres que no parten líneas."""
    chunks, start, pos = [], 0, 0
    for line in text.splitlines(keepends=True):
        if pos - start + len(line) > CHUNK_CHARS and pos > start:
            chunks.append((start, text[start:pos]))
            start = pos
        pos += len(line)
    if pos > start:
        chunks.append((start, text[start:pos]))
    return chunks


def _clean(text: str, start: int, end: int, label: str) -> Entity | None:
    """Quita tratamientos ("Sr. ", "la Sra.") y descarta organismos públicos."""
    span = text[start:end]
    while True:
        m = re.match(r"\s*([\w']+)\.?\s+", span)
        if m and fold(m.group(1)).rstrip("'") in {fold(h).rstrip("'") for h in HONORIFICS}:
            start += m.end()
            span = text[start:end]
            continue
        break
    span = span.rstrip(" .,;:")
    end = start + len(span)
    if len(span) < 2 or fold(span) in {fold(h) for h in HONORIFICS}:
        return None
    if not any(c.isupper() for c in span):
        return None  # "el jutge", "deutor"...
    if label == "EMPRESA" and fold(span).startswith(tuple(fold(p) for p in PUBLIC_BODIES)):
        return None
    if fold(span) in LEGAL_ROLES:
        return None  # "Demandat" en una celda de tabla, "ACTORA"...
    return Entity(start, end, span, label)


def _join_elisions(spans: list[tuple[int, int, str]], text: str) -> list[tuple[int, int, str]]:
    """ "Martí d'" + "Orriols" -> "Martí d'Orriols" (el modelo a veces corta en el apóstrofo)."""
    joined: list[tuple[int, int, str]] = []
    for start, end, kind in spans:
        if joined:
            prev_start, prev_end, prev_kind = joined[-1]
            between = text[prev_end:start]
            if fold(text[max(prev_start, prev_end - 2) : prev_end]) in ELISIONS and not between:
                joined[-1] = (prev_start, end, prev_kind)
                continue
            if between == "'" and fold(text[prev_end - 1 : prev_end]) in {"d", "l"}:
                joined[-1] = (prev_start, end, prev_kind)
                continue
        joined.append((start, end, kind))
    return joined


def detect(text: str) -> list[Entity]:
    """Personas y empresas del texto. Vacío si el modelo no está instalado."""
    if not is_available():
        return []
    model = _get_model()
    # Mismo largo que el original: los offsets siguen sirviendo. Word usa ’ y el modelo
    # se entrenó con '.
    normalized = text.translate(_APOSTROPHES)
    entities: list[Entity] = []
    for offset, chunk in _chunks(normalized):
        spans = _join_elisions(model.predict(chunk), chunk)
        for start, end, kind in spans:
            if kind not in LABELS:
                continue
            entity = _clean(text, offset + start, offset + end, LABELS[kind])
            if entity:
                entities.append(entity)
    return entities
