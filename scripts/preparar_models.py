"""Descarga y prepara los modelos locales en `models/` (NO se suben a git).

Solo hace falta una vez en la máquina de desarrollo (con internet). La app luego funciona
sin conexión. Necesita un entorno aparte con las herramientas de conversión:

    python -m venv .venv-models
    .venv-models/Scripts/python -m pip install optimum-onnx onnx onnxruntime transformers torch
    .venv-models/Scripts/python scripts/preparar_models.py

Modelos (licencias en docs/LICENCIAS.md):
- ner-ca: projecte-aina/roberta-base-ca-v2-cased-ner (Apache-2.0) -> ONNX int8 (~125 MB).
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
NER_REPO = "projecte-aina/roberta-base-ca-v2-cased-ner"

ATTRIBUTION = f"""Model: {NER_REPO}
Autors: Projecte AINA / Barcelona Supercomputing Center
Llicència: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
Modificacions: convertit a ONNX i quantitzat a int8 per a l'Anonimitzador.
"""


def prepare_ner() -> None:
    from onnxruntime.quantization import QuantType, quantize_dynamic

    target = MODELS / "ner-ca"
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [sys.executable, "-m", "optimum.commands.optimum_cli", "export", "onnx",
             "--model", NER_REPO, "--task", "token-classification", tmp],
            check=True,
        )  # fmt: skip
        quantize_dynamic(
            str(Path(tmp) / "model.onnx"), str(target / "model.onnx"), weight_type=QuantType.QInt8
        )
        for name in ("tokenizer.json", "config.json"):
            shutil.copy(Path(tmp) / name, target / name)
    (target / "LICENSE-MODEL.txt").write_text(ATTRIBUTION, encoding="utf-8")
    print(f"Model NER preparat a {target}")


if __name__ == "__main__":
    prepare_ner()
