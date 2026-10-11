"""Ventana única de la aplicación: asistente de 4 pasos (documento, lista, sugerencias,
guardar) con barra lateral, más las pantallas de progreso y de resultado."""

import json
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from anonimizador.core import keep_list
from anonimizador.core.guide import default_path as default_guide_path
from anonimizador.core.lang import DEFAULT_LANGUAGE, LANGUAGES, Language
from anonimizador.core.matcher import Term, keep_term
from anonimizador.core.pipeline import (
    SUPPORTED_INPUTS,
    Analysis,
    AnonymizerError,
    DocumentInfo,
    ReadAhead,
    Report,
    analyze,
    anonymize,
    document_info,
    output_formats,
    read_ahead,
)
from anonimizador.i18n import tr
from anonimizador.ui.keep_dialog import KeepDialog
from anonimizador.ui.pages import DocumentPage, SavePage, TermsPage
from anonimizador.ui.sidebar import Sidebar
from anonimizador.ui.status_pages import ProgressPage, ResultPage
from anonimizador.ui.suggestions import SuggestionsPage
from anonimizador.ui.worker import Task, run_in_background

STEP_DOCUMENT, STEP_TERMS, STEP_SUGGESTIONS, STEP_SAVE = range(4)
KEEP_FILE = "no_anonimitzar.json"


def default_keep_path() -> Path:
    """Carpeta de configuración del usuario en este ordenador (%APPDATA% en Windows,
    ~/Library/Application Support en macOS)."""
    folder = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    return Path(folder or Path.home() / ".anonimitzador") / KEEP_FILE


class MainWindow(QMainWindow):
    def __init__(self, settings: QSettings | None = None, keep_path: Path | None = None):
        super().__init__()
        # Nombres y datos que no se anonimizan nunca (la abogada, el despacho...).
        self.keep_path = keep_path or default_keep_path()
        self.keep: list[str] = keep_list.load(self.keep_path)
        # Solo guarda la última carpeta usada; nunca nombres ni contenido de documentos.
        self.settings = settings or QSettings("Anonimitzador", "Anonimitzador")
        self.input_path: Path | None = None
        self.info: DocumentInfo | None = None
        self._read_ahead: ReadAhead | None = None  # OCR anticipado del PDF elegido
        self.language: Language = DEFAULT_LANGUAGE
        self.analysis: Analysis | None = None
        self._analysis_key: tuple | None = None  # con qué datos se hizo el análisis
        self._reviewed = False  # el usuario ya pasó por las sugerencias
        self._extra_terms: list[Term] = []
        self._task: Task | None = None
        self._saved = False  # se llegó al resultado con el documento actual
        self.setAcceptDrops(True)
        self.resize(1100, 760)
        self.setMinimumSize(920, 640)
        self._build()
        self.retranslate()
        self.go_to(STEP_DOCUMENT)

    # --- Construcción ----------------------------------------------------------------

    def _build(self) -> None:
        central = QWidget()
        row = QHBoxLayout(central)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.sidebar = Sidebar(self.go_to, self.set_language, self.edit_keep_list)
        self.sidebar.language.set_value(self.language.code)
        row.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        self.pages.setObjectName("pages")
        self.document_page = DocumentPage(self.choose_file, lambda: self.go_to(STEP_TERMS))
        self.terms_page = TermsPage(
            self.language, lambda: self.go_to(STEP_DOCUMENT), self.start_analysis,
            self.load_list, self.save_list,
        )  # fmt: skip
        self.table = self.terms_page.table
        self.table.changed.connect(self._refresh_steps)
        self.suggestions_page = SuggestionsPage(
            lambda: self.go_to(STEP_TERMS), self.accept_suggestions, self.add_to_keep_list
        )
        self.save_page = SavePage(lambda: self.go_to(STEP_SUGGESTIONS), self.start_anonymize)
        self.progress_page = ProgressPage(self.cancel_task)
        self.result_page = ResultPage(self.open_folder, self.open_output, self.new_document)
        for page in (self.document_page, self.terms_page, self.suggestions_page,
                     self.save_page, self.progress_page, self.result_page):  # fmt: skip
            self.pages.addWidget(page)
        row.addWidget(self.pages, 1)
        self.setCentralWidget(central)
        self.save_page.set_formats((".docx", ".txt"), self.language.code)

    # Accesos directos usados por los tests y por el resto de la ventana.
    @property
    def folder_edit(self):
        return self.save_page.folder_edit

    @property
    def name_edit(self):
        return self.save_page.name_edit

    @property
    def run_button(self):
        return self.save_page.run_button

    def retranslate(self) -> None:
        lang = self.language.code
        self.setWindowTitle(tr(lang, "app_title"))
        self.sidebar.retranslate(lang)
        self.sidebar.set_keep_count(lang, len(self.keep))
        self.document_page.retranslate(lang, self.input_path, self.info)
        self.terms_page.retranslate(lang)
        self.suggestions_page.retranslate(self.language)
        self.save_page.retranslate(lang)
        self.progress_page.retranslate(lang)
        self.result_page.retranslate(self.language)

    def set_language(self, code: str) -> None:
        self.language = LANGUAGES[code]
        self.sidebar.language.set_value(code)
        self.table.set_language(self.language)
        if self.input_path is not None:
            stem = self.input_path.stem
            for other in LANGUAGES.values():  # cambia el sufijo si no se ha tocado
                if self.name_edit.text() == stem + tr(other.code, "anonymized_suffix"):
                    self.name_edit.setText(stem + tr(code, "anonymized_suffix"))
        self.retranslate()
        self._refresh_steps()

    # --- Navegación ------------------------------------------------------------------

    def _current_key(self) -> tuple:
        return (self.input_path, tuple(self.table.entries()), self.language.code,
                tuple(self.keep))  # fmt: skip

    def _analysis_valid(self) -> bool:
        return self.analysis is not None and self._analysis_key == self._current_key()

    def _reachable(self) -> list[bool]:
        has_file = self.input_path is not None
        valid = has_file and self._analysis_valid()
        return [True, has_file, valid, valid and self._reviewed]

    def current_step(self) -> int | None:
        index = self.pages.currentIndex()
        return index if index <= STEP_SAVE else None

    def _refresh_steps(self) -> None:
        reachable = self._reachable()
        done = [
            self.input_path is not None, self._analysis_valid(),
            self._analysis_valid() and self._reviewed, self._saved,
        ]  # fmt: skip
        busy = self.pages.currentWidget() is self.progress_page
        self.sidebar.update_steps(self.current_step(), [r and not busy for r in reachable], done)
        count = len(self.analysis.suggestions) if self._analysis_valid() else None
        self.sidebar.set_badge(count)

    def go_to(self, step: int) -> None:
        if not self._reachable()[step]:
            return
        self.pages.setCurrentIndex(step)
        self._refresh_steps()

    def _show(self, page: QWidget) -> None:
        self.pages.setCurrentWidget(page)
        self._refresh_steps()

    # --- Selección de ficheros --------------------------------------------------------

    def set_input(self, path: Path) -> None:
        self._stop_read_ahead()
        try:
            info = document_info(path)  # antes del OCR anticipado: PyMuPDF, un hilo
        except Exception as error:  # noqa: BLE001 - PDF protegido, dañado...
            self._failed(error)
            return
        self.input_path, self.info = path, info
        # Mientras el usuario rellena la lista, se van leyendo las páginas escaneadas.
        self._read_ahead = read_ahead(path)
        self.sidebar.set_file(path.name)
        self.folder_edit.setText(str(path.parent))
        self.name_edit.setText(path.stem + tr(self.language.code, "anonymized_suffix"))
        self.save_page.set_formats(output_formats(path), self.language.code)
        self.settings.setValue("last_dir", str(path.parent))
        self.document_page.retranslate(self.language.code, path, info)
        self._refresh_steps()

    def choose_file(self) -> None:
        start = self.settings.value("last_dir", str(Path.home()))
        path, _ = QFileDialog.getOpenFileName(
            self, tr(self.language.code, "choose_file"), start,
            tr(self.language.code, "input_filter"),
        )  # fmt: skip
        if path:
            self.set_input(Path(path))

    def _droppable(self, event) -> Path | None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_INPUTS:
                return path
        return None

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 (API de Qt)
        if self.pages.currentWidget() is not self.progress_page and self._droppable(event):
            event.acceptProposedAction()
            self.document_page.drop.set_hover(True)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802 (API de Qt)
        self.document_page.drop.set_hover(False)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 (API de Qt)
        self.document_page.drop.set_hover(False)
        path = self._droppable(event)
        if path is not None:
            self.set_input(path)
            self.go_to(STEP_DOCUMENT)

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
            self.set_language(data["idioma"])
        self.table.clear_rows()
        for original, replacement in entries:
            self.table.add_row(original, replacement)
        if not entries:
            self.table.add_row()

    # --- Lista «No anonimitzar» ----------------------------------------------------------

    def _save_keep(self, items: list[str]) -> None:
        self.keep = keep_list.clean(items)
        keep_list.save(self.keep_path, self.keep)
        self.sidebar.set_keep_count(self.language.code, len(self.keep))

    def edit_keep_list(self) -> None:
        dialog = KeepDialog(self.keep, self.language.code, self)
        if dialog.exec() == KeepDialog.DialogCode.Accepted:
            self._save_keep(dialog.items())
            self._refresh_steps()  # si ha cambiado, hay que volver a analizar

    def add_to_keep_list(self, texts: list[str]) -> None:
        """Desde las sugerencias: el análisis sigue valiendo (esas filas ya se quitaron)."""
        valid = self._analysis_valid()
        self._save_keep(self.keep + texts)
        if valid:
            self._analysis_key = self._current_key()
        self._refresh_steps()

    # --- Análisis y sugerencias ---------------------------------------------------------

    def _user_terms(self) -> list[Term] | None:
        for original, replacement in self.table.entries():
            if not replacement:
                lang = self.language.code
                QMessageBox.warning(
                    self,
                    tr(lang, "err_title"),
                    tr(lang, "err_empty_replacement", original=original),
                )
                return None
        return [Term(o, r) for o, r in self.table.entries()] + [keep_term(k) for k in self.keep]

    def start_analysis(self) -> None:
        if self.input_path is None:
            return
        terms = self._user_terms()
        if terms is None:
            return
        self._stop_read_ahead()  # el análisis aprovecha lo ya leído
        src, language, key = self.input_path, self.language, self._current_key()
        phases = ["read", "detect"] if self.info and self.info.kind == "pdf" else ["detect"]
        self._run(
            "progress_analyzing", phases,
            lambda progress: analyze(src, terms, language, progress),
            lambda analysis: self._analysis_done(analysis, key, terms),
            back_to=STEP_TERMS,
        )  # fmt: skip

    def _analysis_done(self, analysis: Analysis, key: tuple, terms: list[Term]) -> None:
        self.analysis, self._analysis_key = analysis, key
        self._reviewed = False
        self.suggestions_page.show_analysis(
            analysis, self.language, {t.replacement for t in terms if not t.keep}
        )
        self._show(self.suggestions_page)

    def accept_suggestions(self) -> None:
        self._extra_terms = self.suggestions_page.selected_terms()
        self._reviewed = True
        self.go_to(STEP_SAVE)

    # --- Guardar ----------------------------------------------------------------------

    def output_path(self) -> Path:
        name = self.name_edit.text().strip()
        suffix = self.save_page.formats.value()
        if Path(name).suffix.lower() in (".docx", ".pdf", ".txt"):
            name = Path(name).stem
        return Path(self.folder_edit.text().strip()) / f"{name}{suffix}"

    def _validate_output(self) -> bool:
        lang = self.language.code
        problem = None
        if not self.folder_edit.text().strip() or not Path(self.folder_edit.text()).is_dir():
            problem = tr(lang, "err_no_folder")
        elif not self.name_edit.text().strip():
            problem = tr(lang, "err_no_name")
        if problem:
            QMessageBox.warning(self, tr(lang, "err_title"), problem)
            return False
        out = self.output_path()
        if out.exists():
            answer = QMessageBox.question(
                self, tr(lang, "overwrite_title"), tr(lang, "overwrite", name=out.name)
            )
            return answer == QMessageBox.StandardButton.Yes
        return True

    def start_anonymize(self) -> None:
        if self.input_path is None or not self._validate_output():
            return
        terms = self._user_terms()
        if terms is None:
            return
        terms += self._extra_terms
        src, dst, language = self.input_path, self.output_path(), self.language
        guide = (
            default_guide_path(dst, language) if self.save_page.guide_check.isChecked() else None
        )
        pdf = self.info is not None and self.info.kind == "pdf"
        phases = ["anonymize", "verify"] if pdf else ["anonymize"]
        if pdf and dst.suffix == ".txt":
            phases.append("export")
        self._run(
            "progress_anonymizing", phases,
            lambda progress: anonymize(src, dst, terms, progress, guide, language),
            self._finished, back_to=STEP_SAVE,
        )  # fmt: skip

    # --- Tareas en segundo plano ---------------------------------------------------------

    def _run(self, title_key: str, phases: list[str], fn, on_done, back_to: int) -> None:
        self.progress_page.start(title_key, phases, self.language.code)
        self._show(self.progress_page)

        def finished(result: object) -> None:
            self._task = None
            on_done(result)

        def failed(error: Exception) -> None:
            self._task = None
            self.go_to(back_to)
            self._failed(error)

        def cancelled() -> None:
            self._task = None
            self.go_to(back_to)

        self._task = run_in_background(
            fn, finished, failed, self.progress_page.update_progress, cancelled
        )

    def cancel_task(self) -> None:
        if self._task is not None:
            self._task.cancel()

    def _finished(self, report: Report) -> None:
        self.show_result(report)

    def show_result(self, report: Report) -> None:
        self._saved = True
        self.result_page.show_report(report, self.language)
        self._show(self.result_page)

    def _failed(self, error: Exception) -> None:
        lang = self.language.code
        if isinstance(error, AnonymizerError):
            message = error.message(self.language)
        else:
            message = tr(lang, "error_unexpected", detail=str(error))
        QMessageBox.critical(self, tr(lang, "error_title"), message)

    def open_folder(self) -> None:
        if self.result_page.report:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.result_page.report.output.parent)))

    def open_output(self) -> None:
        if self.result_page.report:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.result_page.report.output)))

    def new_document(self) -> None:
        """Vuelve al paso 1 sin documento (la lista se conserva por si es el mismo caso)."""
        self._stop_read_ahead()
        self.input_path = self.info = self.analysis = self._analysis_key = None
        self._reviewed = self._saved = False
        self._extra_terms = []
        self.sidebar.set_file("")
        self.document_page.retranslate(self.language.code, None, None)
        self.go_to(STEP_DOCUMENT)

    def _stop_read_ahead(self) -> None:
        if self._read_ahead is not None:
            self._read_ahead.stop()
            self._read_ahead = None

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (API de Qt)
        self.cancel_task()
        self._stop_read_ahead()
        super().closeEvent(event)
