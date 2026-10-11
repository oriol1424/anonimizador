"""«Quant a»: versión, qué hace, licencias de terceros y dónde está el código fuente.

Mostrar las licencias y ofrecer el código es obligatorio al entregar la app (LGPL de Qt,
AGPL de PyMuPDF): ver docs/LICENCIAS.md.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
)

from anonimizador import __version__
from anonimizador.i18n import tr
from anonimizador.ui import style
from anonimizador.ui.widgets import button, label

SOURCE_URL = "https://github.com/oriol1424/anonimizador"

THIRD_PARTY = [
    ("Qt / PySide6", "LGPL-3.0"),
    ("PyMuPDF", "AGPL-3.0"),
    ("python-docx", "MIT"),
    ("lxml", "BSD-3-Clause"),
    ("RapidOCR + models PP-OCR", "Apache-2.0"),
    ("ONNX Runtime", "MIT"),
    ("tokenizers (Hugging Face)", "Apache-2.0"),
    ("Model AINA roberta-base-ca-v2-cased-ner (BSC)", "Apache-2.0"),
    ("NumPy", "BSD-3-Clause"),
    ("OpenCV", "Apache-2.0"),
    ("Shapely", "BSD-3-Clause"),
    ("Pillow", "MIT-CMU"),
    ("pyclipper", "MIT"),
    ("omegaconf / PyYAML", "BSD-3-Clause / MIT"),
    ("requests, urllib3, certifi...", "Apache-2.0 / MIT / MPL-2.0"),
]


class AboutDialog(QDialog):
    def __init__(self, lang: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr(lang, "about_button"))
        self.resize(600, 560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(12)

        head = QHBoxLayout()
        head.setSpacing(14)
        logo = QLabel()
        logo.setPixmap(style.app_icon_pixmap(48))
        names = QVBoxLayout()
        names.setSpacing(2)
        names.addWidget(label(tr(lang, "app_title"), "h2"))
        names.addWidget(label(tr(lang, "about_version", version=__version__), "small"))
        head.addWidget(logo)
        head.addLayout(names, 1)
        layout.addLayout(head)
        layout.addWidget(label(tr(lang, "about_text"), "muted", wrap=True))

        layout.addWidget(label(tr(lang, "about_licenses"), "h2"))
        table = QTableWidget(len(THIRD_PARTY), 2)
        table.setHorizontalHeaderLabels([tr(lang, "about_component"), tr(lang, "about_license")])
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for row, (name, lic) in enumerate(THIRD_PARTY):
            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(lic))
        layout.addWidget(table, 1)

        source = label(tr(lang, "about_source", url=SOURCE_URL), "small", wrap=True)
        source.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(source)
        row = QHBoxLayout()
        row.addStretch()
        close = button(tr(lang, "close"), "primary")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        layout.addLayout(row)


class HelpDialog(QDialog):
    """Guía breve: los cuatro pasos, la revisión final, cuánto tarda y la privacidad."""

    def __init__(self, lang: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr(lang, "help_button"))
        self.resize(640, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(12)
        layout.addWidget(label(tr(lang, "help_button"), "h2"))
        self.text = QTextBrowser()
        self.text.setHtml(
            f"<div style='font-size: 10.5pt; color: {style.TEXT}'>{tr(lang, 'help_html')}</div>"
        )
        layout.addWidget(self.text, 1)
        row = QHBoxLayout()
        row.addStretch()
        close = button(tr(lang, "close"), "primary")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        layout.addLayout(row)
