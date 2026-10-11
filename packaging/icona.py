"""Genera el icono de la app (PNG 1024 px) a partir del dibujo de `ui/style.py`.

PyInstaller lo convierte a .ico (Windows) o .icns (macOS) con Pillow.
Uso: python packaging/icona.py <fitxer.png>
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from anonimizador.ui import style  # noqa: E402

app = QApplication([])
pixmap = style.app_icon_pixmap(512)  # ×2 de densidad: 1024 px
pixmap.setDevicePixelRatio(1)
pixmap.save(sys.argv[1], "PNG")
print(f"Icona: {sys.argv[1]}")
