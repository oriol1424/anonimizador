"""Copia los textos de licencia de todo lo que va dentro del paquete.

Uso (en el entorno con el que se construye el paquete):
    python packaging/llicencies.py <carpeta_destino>

- LICENSE del proyecto (AGPL-3.0) y la atribución del modelo de nombres.
- Los ficheros LICENSE/COPYING/NOTICE de cada dependencia instalada (sus dist-info).
- Un índice (LLICENCIES.txt) con nombre, versión y licencia declarada.
"""

import re
import shutil
import sys
from importlib.metadata import distributions
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Herramientas de construcción y de desarrollo: no van dentro del paquete.
SKIP = {
    "pyinstaller", "pyinstaller-hooks-contrib", "altgraph", "pefile", "pywin32-ctypes",
    "macholib", "setuptools", "pip", "wheel", "packaging", "pytest", "pytest-qt", "pluggy",
    "iniconfig", "ruff", "colorama", "pygments", "anonimizador",
}  # fmt: skip
LICENSE_FILE = re.compile(r"(licen[cs]e|copying|notice|authors)", re.I)


def main(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "LICENSE", target / "Anonimitzador-AGPL-3.0.txt")
    model = ROOT / "models" / "ner-ca" / "LICENSE-MODEL.txt"
    if model.exists():
        shutil.copy(model, target / "model-ner-ca-AINA.txt")
    index = [
        "Anonimitzador: AGPL-3.0 (Anonimitzador-AGPL-3.0.txt)",
        "Model de noms projecte-aina/roberta-base-ca-v2-cased-ner: Apache-2.0",
        "",
    ]
    for dist in sorted(distributions(), key=lambda d: d.metadata["Name"].lower()):
        name = dist.metadata["Name"]
        if name.lower() in SKIP:
            continue
        declared = (
            dist.metadata.get("License-Expression")
            or ((dist.metadata.get("License") or "").splitlines() or [""])[0]
        )
        index.append(f"{name} {dist.version}: {declared[:80]}")
        for file in dist.files or []:
            if LICENSE_FILE.search(Path(str(file)).name):
                source = Path(dist.locate_file(file))
                if source.is_file():
                    folder = target / name
                    folder.mkdir(exist_ok=True)
                    shutil.copy(source, folder / source.name)
    (target / "LLICENCIES.txt").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"Llicències copiades a {target}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
