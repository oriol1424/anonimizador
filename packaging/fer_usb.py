"""Monta la carpeta que se copia al USB.

Uso:
    python packaging/fer_usb.py [--windows <zip o carpeta>] [--mac <zip>] [--sortida dist/USB]

Por defecto toma `dist/Anonimitzador` (Windows, construido aquí) y, si existe,
`dist/Anonimitzador-Mac.zip` (descargado de GitHub Actions). Resultado:

    USB/
      Anonimitzador (Windows)/     <- carpeta lista para doble clic
      Anonimitzador (Mac).zip      <- el .app comprimido (descomprimir en el Mac: así
                                      conserva permisos y enlaces, que un USB FAT/exFAT pierde)
      codi_font/anonimizador-<versió>-codi-font.zip   <- obligatorio por la AGPL
      llicencies/                  <- textos de licencia
      LLEGEIX-ME.txt
"""

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from anonimizador import __version__

ROOT = Path(__file__).resolve().parents[1]


def _copy_windows(source: Path, target: Path) -> None:
    if source.suffix == ".zip":
        with zipfile.ZipFile(source) as z:
            z.extractall(target.parent / "_tmp_win")
        inner = next((target.parent / "_tmp_win").iterdir())
        shutil.move(str(inner), target)
        shutil.rmtree(target.parent / "_tmp_win")
    else:
        shutil.copytree(source, target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=Path, default=ROOT / "dist" / "Anonimitzador")
    parser.add_argument("--mac", type=Path, default=ROOT / "dist" / "Anonimitzador-Mac.zip")
    parser.add_argument("--sortida", type=Path, default=ROOT / "dist" / "USB")
    args = parser.parse_args()

    usb = args.sortida
    if usb.exists():
        shutil.rmtree(usb)
    usb.mkdir(parents=True)

    if args.windows.exists():
        _copy_windows(args.windows, usb / "Anonimitzador (Windows)")
        print("Windows: OK")
    else:
        print(f"Windows: no trobat ({args.windows})")
    if args.mac.exists():
        shutil.copy(args.mac, usb / "Anonimitzador (Mac).zip")
        print("Mac: OK")
    else:
        print(f"Mac: no trobat ({args.mac}) - descarrega'l de GitHub Actions")

    source = usb / "codi_font"
    source.mkdir()
    archive = source / f"anonimizador-{__version__}-codi-font.zip"
    subprocess.run(["git", "-C", str(ROOT), "archive", "--format=zip", "-o", str(archive),
                    "HEAD"], check=True)  # fmt: skip
    subprocess.run([sys.executable, str(ROOT / "packaging" / "llicencies.py"),
                    str(usb / "llicencies")], check=True)  # fmt: skip
    readme = (ROOT / "packaging" / "LLEGEIX-ME.txt").read_text(encoding="utf-8")
    (usb / "LLEGEIX-ME.txt").write_text(readme.replace("{version}", __version__),
                                        encoding="utf-8")  # fmt: skip
    print(f"USB preparat a {usb}")


if __name__ == "__main__":
    main()
