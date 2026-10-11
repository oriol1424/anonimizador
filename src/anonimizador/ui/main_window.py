"""Ventana única de la aplicación: documento, qué anonimizar, dónde guardar y un botón."""

import json
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from anonimizador.core.guide import default_path as default_guide_path
from anonimizador.core.lang import DEFAULT_LANGUAGE, LANGUAGES, Language
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import (
    SUPPORTED_INPUTS,
    Analysis,
    AnonymizerError,
    ReadAhead,
    Report,
    analyze,
    anonymize,
    output_formats,
    read_ahead,
)
from anonimizador.i18n import tr
from anonimizador.ui.suggestions import SuggestionsDialog
from anonimizador.ui.widgets import ReplacementCombo
from anonimizador.ui.worker import run_in_background

FORMAT_LABELS = {".docx": "format_docx", ".pdf": "format_pdf", ".txt": "format_txt"}


class TermsTable(QTableWidget):
    """Tabla "Text original | Substituir per"."""

    def __init__(self, language: Language):
        super().__init__(0, 2)
        self._language = language
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.setColumnWidth(1, 220)

    def combo(self, row: int) -> ReplacementCombo:
        return self.cellWidget(row, 1)

    def add_row(self, original: str = "", replacement: str | None = None) -> int:
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(original))
        combo = ReplacementCombo(self._language, self.aliases_except)
        self.setCellWidget(row, 1, combo)
        if replacement is None:
            combo.choose(self._language.presets[0])
        else:
            combo.setEditText(replacement)
        return row

    def remove_selected(self) -> None:
        rows = sorted({i.row() for i in self.selectedIndexes()}, reverse=True)
        if not rows and self.rowCount():
            rows = [self.rowCount() - 1]
        for row in rows:
            self.removeRow(row)

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


class MainWindow(QMainWindow):
    def __init__(self, settings: QSettings | None = None):
        super().__init__()
        # Solo guarda la última carpeta usada; nunca nombres ni contenido de documentos.
        self.settings = settings or QSettings("Anonimitzador", "Anonimitzador")
        self.input_path: Path | None = None
        self._read_ahead: ReadAhead | None = None  # OCR anticipado del PDF elegido
        self.language: Language = DEFAULT_LANGUAGE
        self.setAcceptDrops(True)
        self.resize(820, 680)
        self._build()
        self.retranslate()

    # --- Construcción ----------------------------------------------------------------

    def _build(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        self.doc_box = QGroupBox()
        doc_layout = QVBoxLayout(self.doc_box)
        row = QHBoxLayout()
        self.file_label = QLabel()
        self.file_label.setObjectName("fileLabel")
        self.choose_file_button = QPushButton()
        self.choose_file_button.clicked.connect(self.choose_file)
        row.addWidget(self.file_label, 1)
        row.addWidget(self.choose_file_button)
        doc_layout.addLayout(row)
        row = QHBoxLayout()
        self.language_label = QLabel()
        self.language_combo = QComboBox()
        for lang in LANGUAGES.values():
            self.language_combo.addItem(lang.name, lang.code)
        self.language_combo.setCurrentIndex(self.language_combo.findData(DEFAULT_LANGUAGE.code))
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        row.addWidget(self.language_label)
        row.addWidget(self.language_combo)
        row.addStretch()
        doc_layout.addLayout(row)
        layout.addWidget(self.doc_box)

        self.terms_box = QGroupBox()
        terms_layout = QVBoxLayout(self.terms_box)
        self.terms_hint = QLabel(wordWrap=True)
        self.terms_hint.setObjectName("hint")
        terms_layout.addWidget(self.terms_hint)
        self.table = TermsTable(self.language)
        self.table.add_row()
        terms_layout.addWidget(self.table)
        row = QHBoxLayout()
        self.add_button = QPushButton()
        self.add_button.clicked.connect(lambda: self.table.add_row())
        self.remove_button = QPushButton()
        self.remove_button.clicked.connect(self.table.remove_selected)
        self.load_button = QPushButton()
        self.load_button.clicked.connect(self.load_list)
        self.save_list_button = QPushButton()
        self.save_list_button.clicked.connect(self.save_list)
        for b in (self.add_button, self.remove_button):
            row.addWidget(b)
        row.addStretch()
        for b in (self.load_button, self.save_list_button):
            row.addWidget(b)
        terms_layout.addLayout(row)
        layout.addWidget(self.terms_box, 1)

        self.output_box = QGroupBox()
        form = QFormLayout(self.output_box)
        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.choose_folder_button = QPushButton()
        self.choose_folder_button.clicked.connect(self.choose_folder)
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(self.choose_folder_button)
        self.name_edit = QLineEdit()
        self.format_combo = QComboBox()
        self.folder_label, self.name_label, self.format_label = QLabel(), QLabel(), QLabel()
        form.addRow(self.folder_label, folder_row)
        form.addRow(self.name_label, self.name_edit)
        form.addRow(self.format_label, self.format_combo)
        self.guide_check = QCheckBox()
        self.guide_check.setChecked(True)
        form.addRow("", self.guide_check)
        layout.addWidget(self.output_box)

        self.run_button = QPushButton()
        self.run_button.setObjectName("primary")
        self.run_button.setMinimumHeight(44)
        self.run_button.clicked.connect(self.start)
        layout.addWidget(self.run_button)

        self.setCentralWidget(central)

    def retranslate(self) -> None:
        lang = self.language.code
        self.setWindowTitle(tr(lang, "app_title"))
        self.doc_box.setTitle(tr(lang, "document"))
        if self.input_path is None:
            self.file_label.setText(tr(lang, "no_file"))
        self.choose_file_button.setText(tr(lang, "choose_file"))
        self.language_label.setText(tr(lang, "language"))
        self.terms_box.setTitle(tr(lang, "terms"))
        self.terms_hint.setText(tr(lang, "terms_hint"))
        self.table.setHorizontalHeaderLabels(
            [tr(lang, "col_original"), tr(lang, "col_replacement")]
        )
        self.add_button.setText(tr(lang, "add_row"))
        self.remove_button.setText(tr(lang, "remove_row"))
        self.load_button.setText(tr(lang, "load_list"))
        self.save_list_button.setText(tr(lang, "save_list"))
        self.output_box.setTitle(tr(lang, "save_as"))
        self.folder_label.setText(tr(lang, "folder"))
        self.choose_folder_button.setText(tr(lang, "choose_folder"))
        self.name_label.setText(tr(lang, "file_name"))
        self.format_label.setText(tr(lang, "format"))
        self.guide_check.setText(tr(lang, "save_guide"))
        self._refresh_formats()
        self.run_button.setText(tr(lang, "anonymize"))

    def _refresh_formats(self) -> None:
        """Formatos según el documento de entrada: Word -> Word/Text, PDF -> PDF/Text."""
        current = self.format_combo.currentData()
        formats = output_formats(self.input_path) if self.input_path else (".docx", ".txt")
        self.format_combo.clear()
        for suffix in formats:
            self.format_combo.addItem(tr(self.language.code, FORMAT_LABELS[suffix]), suffix)
        index = self.format_combo.findData(current)
        self.format_combo.setCurrentIndex(max(index, 0))

    def _on_language_changed(self) -> None:
        self.language = LANGUAGES[self.language_combo.currentData()]
        self.table.set_language(self.language)
        self.retranslate()

    # --- Selección de ficheros --------------------------------------------------------

    def set_input(self, path: Path) -> None:
        self._stop_read_ahead()
        self.input_path = path
        # Mientras el usuario rellena la lista, se van leyendo las páginas escaneadas.
        self._read_ahead = read_ahead(path)
        self.file_label.setText(str(path))
        if not self.folder_edit.text():
            self.folder_edit.setText(str(path.parent))
        self.name_edit.setText(path.stem + tr(self.language.code, "anonymized_suffix"))
        self._refresh_formats()
        self.settings.setValue("last_dir", str(path.parent))

    def choose_file(self) -> None:
        start = self.settings.value("last_dir", str(Path.home()))
        path, _ = QFileDialog.getOpenFileName(
            self, tr(self.language.code, "choose_file"), start,
            tr(self.language.code, "input_filter"),
        )  # fmt: skip
        if path:
            self.set_input(Path(path))

    def choose_folder(self) -> None:
        start = self.folder_edit.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(
            self, tr(self.language.code, "choose_folder"), start
        )
        if folder:
            self.folder_edit.setText(folder)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 (API de Qt)
        if any(Path(u.toLocalFile()).suffix.lower() in SUPPORTED_INPUTS
               for u in event.mimeData().urls()):  # fmt: skip
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 (API de Qt)
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_INPUTS:
                self.set_input(path)
                break

    # --- Listas de términos (plantillas por caso) -------------------------------------

    def save_list(self) -> None:
        lang = self.language.code
        path, _ = QFileDialog.getSaveFileName(
            self, tr(lang, "save_list"), self.settings.value("last_dir", ""),
            tr(lang, "list_filter"),
        )  # fmt: skip
        if not path:
            return
        data = {
            "idioma": self.language.code,
            "termes": [{"original": o, "substitut": r} for o, r in self.table.entries()],
        }
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_list(self) -> None:
        lang = self.language.code
        path, _ = QFileDialog.getOpenFileName(
            self, tr(lang, "load_list"), self.settings.value("last_dir", ""),
            tr(lang, "list_filter"),
        )  # fmt: skip
        if path:
            self.load_list_file(Path(path))

    def load_list_file(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entries = [(t["original"], t["substitut"]) for t in data["termes"]]
        except (OSError, ValueError, KeyError, TypeError):
            QMessageBox.warning(
                self, tr(self.language.code, "error_title"),
                tr(self.language.code, "error_bad_list"),
            )  # fmt: skip
            return
        if data.get("idioma") in LANGUAGES:
            self.language_combo.setCurrentIndex(self.language_combo.findData(data["idioma"]))
        self.table.clear_rows()
        for original, replacement in entries:
            self.table.add_row(original, replacement)
        if not entries:
            self.table.add_row()

    # --- Proceso ----------------------------------------------------------------------

    def output_path(self) -> Path:
        name = self.name_edit.text().strip()
        suffix = self.format_combo.currentData()
        if Path(name).suffix.lower() in FORMAT_LABELS:
            name = Path(name).stem
        return Path(self.folder_edit.text().strip()) / f"{name}{suffix}"

    def _validate(self) -> list[Term] | None:
        lang = self.language.code
        problem = None
        if self.input_path is None:
            problem = tr(lang, "err_no_file")
        elif not self.folder_edit.text().strip() or not Path(self.folder_edit.text()).is_dir():
            problem = tr(lang, "err_no_folder")
        elif not self.name_edit.text().strip():
            problem = tr(lang, "err_no_name")
        else:
            for original, replacement in self.table.entries():
                if not replacement:
                    problem = tr(lang, "err_empty_replacement", original=original)
                    break
        if problem:
            QMessageBox.warning(self, tr(lang, "err_title"), problem)
            return None
        out = self.output_path()
        if out.exists():
            answer = QMessageBox.question(
                self, tr(lang, "overwrite_title"), tr(lang, "overwrite", name=out.name)
            )
            if answer != QMessageBox.StandardButton.Yes:
                return None
        return [Term(o, r) for o, r in self.table.entries()]

    def _set_busy(self, busy: bool) -> None:
        self.centralWidget().setEnabled(not busy)
        self.run_button.setText(tr(self.language.code, "working" if busy else "anonymize"))
        if busy:
            self.setCursor(Qt.CursorShape.WaitCursor)
        else:
            self.unsetCursor()

    def _stop_read_ahead(self) -> None:
        if self._read_ahead is not None:
            self._read_ahead.stop()
            self._read_ahead = None

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (API de Qt)
        self._stop_read_ahead()
        super().closeEvent(event)

    def start(self) -> None:
        terms = self._validate()
        if terms is None:
            return
        self._stop_read_ahead()  # el análisis aprovecha lo ya leído
        src, dst, language = self.input_path, self.output_path(), self.language
        guide = default_guide_path(dst, language) if self.guide_check.isChecked() else None
        self._set_busy(True)

        def after_analysis(analysis: Analysis) -> None:
            extra = self.ask_suggestions(analysis, terms)
            if extra is None:
                self._set_busy(False)
                return
            run_in_background(
                lambda progress: anonymize(src, dst, terms + extra, progress, guide, language),
                self._finished,
                self._failed,
                self._show_progress,
            )

        run_in_background(
            lambda progress: analyze(src, terms, language, progress),
            after_analysis,
            self._failed,
            self._show_progress,
        )

    def _show_progress(self, done: int, total: int) -> None:
        self.run_button.setText(tr(self.language.code, "ocr_progress", done=done, total=total))

    def ask_suggestions(self, analysis: Analysis, terms: list[Term]) -> list[Term] | None:
        """Términos extra aceptados por el usuario, o None si cancela."""
        if not analysis.suggestions and not analysis.notices:
            return []
        dialog = SuggestionsDialog(analysis, self.language, {t.replacement for t in terms}, self)
        if dialog.exec() != SuggestionsDialog.DialogCode.Accepted:
            return None
        return dialog.selected_terms()

    def _finished(self, report: Report) -> None:
        self._set_busy(False)
        self.show_result(report)

    def _failed(self, error: Exception) -> None:
        self._set_busy(False)
        lang = self.language.code
        if isinstance(error, AnonymizerError):
            message = error.message(self.language)
        else:
            message = tr(lang, "error_unexpected", detail=str(error))
        QMessageBox.critical(self, tr(lang, "error_title"), message)

    def show_result(self, report: Report) -> None:
        lang = self.language.code
        box = QMessageBox(self)
        box.setWindowTitle(tr(lang, "done_title"))
        text = tr(lang, "done", path=report.output, total=report.total)
        if report.guide:
            text += "\n\n" + tr(lang, "guide_saved", path=report.guide)
        if report.notices:
            leak = any(n.is_leak for n in report.notices)
            box.setIcon(QMessageBox.Icon.Critical if leak else QMessageBox.Icon.Warning)
            notices = sorted(report.notices, key=lambda n: not n.is_leak)  # fugas primero
            text += f"\n\n{tr(lang, 'warnings')}:\n" + "\n".join(
                f"• {n.message(self.language)}" for n in notices
            )
        else:
            box.setIcon(QMessageBox.Icon.Information)
        box.setText(text)
        open_button = box.addButton(tr(lang, "open_folder"), QMessageBox.ButtonRole.ActionRole)
        box.addButton(tr(lang, "close"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(report.output.parent)))
