"""Pantallas de los pasos 1 (documento), 2 (lista) y 4 (guardar)."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from anonimizador.core.lang import Language
from anonimizador.core.pipeline import DocumentInfo
from anonimizador.i18n import tr
from anonimizador.ui import style
from anonimizador.ui.widgets import ReplacementCombo, Segmented, button, card, label, set_prop

FORMAT_LABELS = {".docx": "format_docx", ".pdf": "format_pdf", ".txt": "format_text_short"}
# Carpetas que se sincronizan con la nube (por nombre de la ruta).
CLOUD_MARKERS = ("onedrive", "dropbox", "google drive", "googledrive", "icloud",
                 "mobile documents", "nextcloud", "pcloud", "box sync")  # fmt: skip


def is_cloud_folder(folder: str) -> bool:
    lowered = folder.replace("\\", "/").lower()
    return any(marker in lowered for marker in CLOUD_MARKERS)


class NoticeLabel(QLabel):
    """Aviso amarillo de una línea (o varias) dentro de una pantalla."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("inlineWarning")
        self.setWordWrap(True)
        self.hide()


class Page(QWidget):
    """Pantalla con título, subtítulo, contenido y una fila de botones abajo."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("page")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 30, 36, 24)
        outer.setSpacing(16)
        self.title = label("", "h1")
        self.intro = label("", "muted", wrap=True)
        head = QVBoxLayout()
        head.setSpacing(4)
        head.addWidget(self.title)
        head.addWidget(self.intro)
        outer.addLayout(head)
        self.body = QVBoxLayout()
        self.body.setSpacing(14)
        outer.addLayout(self.body, 1)
        self.footer = QHBoxLayout()
        self.footer.setSpacing(10)
        outer.addLayout(self.footer)


# --- Paso 1: documento -------------------------------------------------------------------


class DropZone(QFrame):
    """Zona para arrastrar el fichero (la ventana entera también lo acepta)."""

    def __init__(self, on_choose: Callable[[], None]):
        super().__init__()
        self.setObjectName("dropzone")
        self.setMinimumHeight(260)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addStretch()
        mark = QLabel()
        mark.setPixmap(style.icon_pixmap("upload", style.ACCENT, 40, 1.6))
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text = label("", "h2")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.or_label = label("", "small")
        self.or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.choose = button("", "primary")
        self.choose.clicked.connect(on_choose)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.choose)
        row.addStretch()
        for w in (mark, self.text, self.or_label):
            layout.addWidget(w)
        layout.addLayout(row)
        layout.addStretch()

    def set_hover(self, hover: bool) -> None:
        set_prop(self, "hover", hover)


class DocumentPage(Page):
    def __init__(self, on_choose: Callable[[], None], on_continue: Callable[[], None]):
        super().__init__()
        self.drop = DropZone(on_choose)
        self.body.addWidget(self.drop)

        self.file_card, card_layout = card()
        row = QHBoxLayout()
        row.setSpacing(14)
        icon = QLabel()
        icon.setFixedSize(44, 44)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"background: {style.ACCENT_SOFT}; border-radius: 8px;")
        icon.setPixmap(style.icon_pixmap("file", style.ACCENT, 22, 1.8))
        names = QVBoxLayout()
        names.setSpacing(2)
        self.file_name = label("", "h2")
        self.file_name.setTextFormat(Qt.TextFormat.PlainText)
        self.file_details = label("", "small")
        self.file_folder = label("", "small")
        for w in (self.file_name, self.file_details, self.file_folder):
            w.setTextFormat(Qt.TextFormat.PlainText)
            names.addWidget(w)
        self.change = button("")
        self.change.clicked.connect(on_choose)
        row.addWidget(icon)
        row.addLayout(names, 1)
        row.addWidget(self.change)
        card_layout.addLayout(row)
        self.body.addWidget(self.file_card)
        self.file_card.hide()
        self.body.addStretch()

        self.footer.addStretch()
        self.continue_button = button("", "primary")
        self.continue_button.clicked.connect(on_continue)
        self.continue_button.setEnabled(False)
        self.footer.addWidget(self.continue_button)

    def retranslate(self, lang: str, path: Path | None, info: DocumentInfo | None) -> None:
        self.title.setText(tr(lang, "doc_title"))
        self.intro.setText(tr(lang, "doc_intro"))
        self.drop.text.setText(tr(lang, "drop_here"))
        self.drop.or_label.setText(tr(lang, "drop_or"))
        self.drop.choose.setText(tr(lang, "choose_file"))
        self.change.setText(tr(lang, "change_file"))
        self.continue_button.setText(tr(lang, "continue"))
        if path is not None and info is not None:
            if info.kind == "pdf" and info.scanned:
                kind = tr(lang, "file_pdf_scanned", pages=info.pages, scanned=info.scanned)
            elif info.kind == "pdf":
                kind = tr(lang, "file_pdf", pages=info.pages)
            else:
                kind = tr(lang, "file_word")
            self.file_name.setText(path.name)
            self.file_details.setText(kind)
            # La carpeta puede ser muy larga: se recorta por el medio (entera en la ayuda).
            metrics = self.file_folder.fontMetrics()
            self.file_folder.setText(
                metrics.elidedText(str(path.parent), Qt.TextElideMode.ElideMiddle, 520)
            )
            self.file_folder.setToolTip(str(path))
        self.file_card.setVisible(path is not None)
        self.drop.setVisible(path is None)
        self.continue_button.setEnabled(path is not None)


# --- Paso 2: lista -----------------------------------------------------------------------


class TermsTable(QTableWidget):
    """Tabla "Text original | Substituir per"."""

    changed = Signal()

    def __init__(self, language: Language):
        super().__init__(0, 2)
        self._language = language
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(42)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setColumnWidth(1, 260)
        self.itemChanged.connect(lambda _: self.changed.emit())

    def combo(self, row: int) -> ReplacementCombo:
        return self.cellWidget(row, 1)

    def add_row(self, original: str = "", replacement: str | None = None) -> int:
        row = self.rowCount()
        self.blockSignals(True)  # sin avisos hasta que la fila tenga su desplegable
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(original))
        combo = ReplacementCombo(self._language, self.aliases_except)
        self.setCellWidget(row, 1, combo)
        self.blockSignals(False)
        if replacement is None:
            combo.choose(self._language.presets[0])
        else:
            combo.setEditText(replacement)
        combo.editTextChanged.connect(lambda _: self.changed.emit())
        self.changed.emit()
        return row

    def remove_selected(self) -> None:
        rows = sorted({i.row() for i in self.selectedIndexes()}, reverse=True)
        if not rows and self.rowCount():
            rows = [self.rowCount() - 1]
        for row in rows:
            self.removeRow(row)
        self.changed.emit()

    def aliases_except(self, combo: ReplacementCombo | None = None) -> set[str]:
        return {self.combo(r).value() for r in range(self.rowCount()) if self.combo(r) is not combo}

    def set_language(self, language: Language) -> None:
        self._language = language
        for r in range(self.rowCount()):
            self.combo(r).set_language(language)

    def entries(self) -> list[tuple[str, str]]:
        """Filas con texto original (las vacías se ignoran)."""
        result = []
        for r in range(self.rowCount()):
            item = self.item(r, 0)
            original = item.text().strip() if item else ""
            if original:
                result.append((original, self.combo(r).value()))
        return result

    def clear_rows(self) -> None:
        self.setRowCount(0)
        self.changed.emit()


class TermsPage(Page):
    def __init__(self, language: Language, on_back, on_analyze, on_load, on_save):
        super().__init__()
        self.table = TermsTable(language)
        self.table.add_row()
        self.body.addWidget(self.table, 1)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.add_button = button("")
        self.add_button.clicked.connect(lambda: self.table.add_row())
        self.remove_button = button("", "flat")
        self.remove_button.clicked.connect(self.table.remove_selected)
        self.load_button = button("")
        self.load_button.clicked.connect(on_load)
        self.save_list_button = button("")
        self.save_list_button.clicked.connect(on_save)
        row.addWidget(self.add_button)
        row.addWidget(self.remove_button)
        row.addStretch()
        row.addWidget(self.load_button)
        row.addWidget(self.save_list_button)
        self.body.addLayout(row)

        self.back_button = button("")
        self.back_button.clicked.connect(on_back)
        self.analyze_button = button("", "primary")
        self.analyze_button.clicked.connect(on_analyze)
        self.footer.addWidget(self.back_button)
        self.footer.addStretch()
        self.footer.addWidget(self.analyze_button)

    def retranslate(self, lang: str) -> None:
        self.title.setText(tr(lang, "terms"))
        self.intro.setText(tr(lang, "terms_hint"))
        self.table.setHorizontalHeaderLabels(
            [tr(lang, "col_original"), tr(lang, "col_replacement")]
        )
        self.add_button.setText(tr(lang, "add_row"))
        self.remove_button.setText(tr(lang, "remove_row"))
        self.load_button.setText(tr(lang, "load_list"))
        self.save_list_button.setText(tr(lang, "save_list"))
        self.back_button.setText(tr(lang, "back"))
        self.analyze_button.setText(tr(lang, "analyze"))


# --- Paso 4: guardar ---------------------------------------------------------------------


class SavePage(Page):
    def __init__(self, on_back, on_run):
        super().__init__()
        box, layout = card()
        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.choose_folder_button = button("")
        self.choose_folder_button.clicked.connect(self.choose_folder)
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(self.choose_folder_button)
        self.name_edit = QLineEdit()
        self.formats = Segmented([], lambda _: None)
        self._formats_row = QHBoxLayout()
        self._formats_row.addWidget(self.formats)
        self._formats_row.addStretch()
        self.folder_label, self.name_label, self.format_label = QLabel(), QLabel(), QLabel()
        form.addRow(self.folder_label, folder_row)
        form.addRow(self.name_label, self.name_edit)
        form.addRow(self.format_label, self._formats_row)
        layout.addLayout(form)
        self.guide_check = QCheckBox()
        self.guide_check.setChecked(True)
        layout.addWidget(self.guide_check)
        self.body.addWidget(box)
        # Carpeta sincronizada con la nube: la guía (con los nombres reales) se subiría.
        self.cloud_warning = NoticeLabel()
        self.body.addWidget(self.cloud_warning)
        self.folder_edit.textChanged.connect(lambda _: self._update_cloud_warning())
        self.guide_check.toggled.connect(lambda _: self._update_cloud_warning())
        self.body.addStretch()

        self.back_button = button("")
        self.back_button.clicked.connect(on_back)
        self.run_button = button("", "primary")
        self.run_button.clicked.connect(on_run)
        self.footer.addWidget(self.back_button)
        self.footer.addStretch()
        self.footer.addWidget(self.run_button)
        self._lang = "ca"

    def set_formats(self, formats: tuple[str, ...], lang: str) -> None:
        """Formatos según el documento: Word -> Word/Text, PDF -> PDF/Text. Se conserva la
        elección si sigue siendo posible."""
        current = self.formats.value()
        self._formats_row.removeWidget(self.formats)
        self.formats.deleteLater()
        self.formats = Segmented([(tr(lang, FORMAT_LABELS[f]), f) for f in formats],
                                 lambda _: None)  # fmt: skip
        self._formats_row.insertWidget(0, self.formats)
        self.formats.set_value(current if current in formats else formats[0])

    def _update_cloud_warning(self) -> None:
        show = self.guide_check.isChecked() and is_cloud_folder(self.folder_edit.text())
        self.cloud_warning.setText(tr(self._lang, "cloud_warning"))
        self.cloud_warning.setVisible(show)

    def choose_folder(self) -> None:
        start = self.folder_edit.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, tr(self._lang, "choose_folder"), start)
        if folder:
            self.folder_edit.setText(folder)

    def retranslate(self, lang: str) -> None:
        self._lang = lang
        self.title.setText(tr(lang, "save_title"))
        self.intro.setText(tr(lang, "save_intro"))
        self.folder_label.setText(tr(lang, "folder"))
        self.choose_folder_button.setText(tr(lang, "choose_folder"))
        self.name_label.setText(tr(lang, "file_name"))
        self.format_label.setText(tr(lang, "format"))
        self.guide_check.setText(tr(lang, "save_guide"))
        for suffix, b in self.formats.buttons.items():
            b.setText(tr(lang, FORMAT_LABELS[suffix]))
        self.back_button.setText(tr(lang, "back"))
        self.run_button.setText(tr(lang, "anonymize"))
        self._update_cloud_warning()
