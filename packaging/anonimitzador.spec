# Receta de PyInstaller: carpeta (Windows) o .app (macOS) con todo dentro.
#   python packaging/icona.py build/icona.png
#   pyinstaller packaging/anonimitzador.spec --noconfirm
# El modelo de nombres debe estar en models/ner-ca (scripts/preparar_models.py).
# --onedir (no un único .exe): Qt queda enlazado dinámicamente, como pide la LGPL.

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

ROOT = Path(SPECPATH).parent
MAC = sys.platform == "darwin"
ICON = ROOT / "build" / "icona.png"
MODEL = ROOT / "models" / "ner-ca"
if not (MODEL / "model.onnx").exists():
    raise SystemExit(f"Falta el model de noms a {MODEL} (scripts/preparar_models.py)")

datas = collect_data_files("rapidocr")  # configuración y modelos del OCR
datas += [(str(MODEL), "models/ner-ca"), (str(ROOT / "LICENSE"), ".")]

a = Analysis(
    [str(ROOT / "packaging" / "entrada.py")],
    pathex=[str(ROOT / "src")],
    binaries=collect_dynamic_libs("onnxruntime"),
    datas=datas,
    hiddenimports=collect_submodules("rapidocr") + ["anonimizador.core.selftest"],
    excludes=[
        "tkinter", "pytest", "IPython", "matplotlib",
        # Solo PySide6-Essentials: ni WebEngine (Chromium) ni Qml/Quick/Pdf/3D/Multimedia.
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebChannel",
        "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
        "PySide6.Qt3DCore", "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtNetwork",
        # Red: la app no la usa (los modelos van dentro).
        "huggingface_hub", "hf_xet", "httpx", "httpx2", "httpcore2",
    ],
    noarchive=False,
)
# Bibliotecas y plugins de Qt que arrastran los plugins por defecto y la app no usa: teclado
# virtual (Qml/Quick), visor PDF de Qt, red (TLS) y OpenGL por software.
DROP = ("Qt6Pdf", "Qt6Qml", "Qt6Quick", "Qt6VirtualKeyboard", "Qt6Network", "QtNetwork",
        "opengl32sw", "qtvirtualkeyboard", "qpdf", "networkinformation", "qopensslbackend",
        "qschannelbackend", "qcertonlybackend")  # fmt: skip
a.binaries = [b for b in a.binaries if not any(d.lower() in b[0].lower() for d in DROP)]
# Traducciones de Qt: solo catalán y castellano.
a.datas = [
    d for d in a.datas
    if "translations" not in d[0] or any(f"_{lang}.qm" in d[0] for lang in ("ca", "es"))
]  # fmt: skip

pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="Anonimitzador",
    console=False, icon=str(ICON) if ICON.exists() else None,
    argv_emulation=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="Anonimitzador")

if MAC:
    app = BUNDLE(
        coll, name="Anonimitzador.app", icon=str(ICON) if ICON.exists() else None,
        bundle_identifier="cat.anonimitzador.app",
        info_plist={
            "CFBundleName": "Anonimitzador",
            "CFBundleDisplayName": "Anonimitzador",
            "CFBundleShortVersionString": __import__("anonimizador").__version__,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "12.0",
            "NSHumanReadableCopyright": "Llicència AGPL-3.0. Codi font a la carpeta codi_font.",
        },
    )
