"""Ventana única de la aplicación: asistente de 4 pasos (documento, lista, sugerencias,
guardar) con barra lateral, más las pantallas de progreso y de resultado."""

import json
import re
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from anonimizador.core import errlog, estimate, keep_list, ner, review
from anonimizador.core.guide import default_path as default_guide_path
from anonimizador.core.lang import DEFAULT_LANGUAGE, LANGUAGES, Language, fill_preset
from anonimizador.core.matcher import Matcher, Term, keep_term
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
from anonimizador.ui import style
from anonimizador.ui.about_dialog import AboutDialog, HelpDialog
from anonimizador.ui.keep_dialog import KeepDialog
from anonimizador.ui.pages import DocumentPage, SavePage, TermsPage
from anonimizador.ui.review_dialog import ReviewDialog
from anonimizador.ui.sidebar import Sidebar
from anonimizador.ui.status_pages import ProgressPage, ResultPage
from anonimizador.ui.suggestions import SuggestionsPage
from anonimizador.ui.worker import Task, run_in_background

STEP_DOCUMENT, STEP_TERMS, STEP_SUGGESTIONS, STEP_SAVE = range(4)
KEEP_FILE = "no_anonimitzar.json"
LOG_FILE = "errors.log"


def config_dir() -> Path:
    """Carpeta de configuración del usuario en este ordenador (%APPDATA% en Windows,
    ~/Library/Application Support en macOS)."""
    folder = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    return Path(folder or Path.home() / ".anonimitzador")


def default_keep_path() -> Path:
    return config_dir() / KEEP_FILE


class MainWindow(QMainWindow):
    def __init__(self, keep_path: Path | None = None, log_path: Path | None = None):
        super().__init__()
        # Registro de errores sin texto del documento (core/errlog.py).
        self.log_path = log_path or config_dir() / LOG_FILE
        self._step = ""  # qué se estaba haciendo, para el registro
        # Nombres y datos que no se anonimizan nunca (la abogada, el despacho...).
        self.keep_path = keep_path or default_keep_path()
        self.keep: list[str] = keep_list.load(self.keep_path)
        # Última carpeta usada, solo mientras la app está abierta: su nombre puede ser el
        # del cliente, así que no se guarda en la configuración del sistema.
        self._last_dir = str(Path.home())
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
        self.setWindowIcon(style.app_icon())
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
        self.sidebar = Sidebar(self.go_to, self.set_language, self.edit_keep_list,
                               self.show_about, self.show_help)  # fmt: skip
        self.sidebar.language.set_value(self.language.code)
        row.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        self.pages.setObjectName("pages")
        self.document_page = DocumentPage(self.choose_file, lambda: self.go_to(STEP_TERMS))
        self.terms_page = TermsPage(
            self.language, lambda: self.go_to(STEP_DOCUMENT), self.start_analysis,
            self.load_list, self.save_list,
        )  # fmt: skip
        self.document_page.help_link.clicked.connect(self.show_help)
        self.table = self.terms_page.table
        self.table.changed.connect(self._refresh_steps)
        self.suggestions_page = SuggestionsPage(
            lambda: self.go_to(STEP_TERMS), self.accept_suggestions, self.add_to_keep_list
        )
        self.save_page = SavePage(lambda: self.go_to(STEP_SUGGESTIONS), self.start_anonymize)
        self.progress_page = ProgressPage(self.cancel_task)
        self.result_page = ResultPage(
            self.open_folder, self.open_output, self.new_document, self.review_output
        )
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
        self.document_page.retranslate(lang, self.input_path, self.info, self._estimate_total())
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
        self._step = "open_document"
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
        self._last_dir = str(path.parent)
        self.document_page.retranslate(self.language.code, path, info, self._estimate_total())
        self._refresh_steps()

    def choose_file(self) -> None:
        start = self._last_dir
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
            self, tr(lang, "save_list"), self._last_dir,
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
            self, tr(lang, "load_list"), self._last_dir,
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
        phases = ["read", "detect"]  # Word: "read" son sus imágenes (OCR)
        estimates = estimate.analysis(self.info.workload, ner.is_available())
        self._run(
            "progress_analyzing", phases,
            lambda progress: analyze(src, terms, language, progress),
            lambda analysis: self._analysis_done(analysis, key, terms),
            back_to=STEP_TERMS, estimates=estimates,
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
        existing = [p.name for p in (out, self._guide_path(out)) if p and p.exists()]
        if existing:
            answer = QMessageBox.question(
                self, tr(lang, "overwrite_title"), tr(lang, "overwrite", name="», «".join(existing))
            )
            return answer == QMessageBox.StandardButton.Yes
        return True

    def _guide_path(self, out: Path) -> Path | None:
        if not self.save_page.guide_check.isChecked():
            return None
        return default_guide_path(out, self.language)

    def start_anonymize(self) -> None:
        if self.input_path is None:
            return
        terms = self._user_terms()
        if terms is None:
            return
        terms += self._extra_terms
        # El nombre del fichero también llega a la IA: «Demanda Joan Puig» -> «Demanda
        # [CLIENT_1]». Se cambia a la vista del usuario antes de guardar.
        name = self.name_edit.text().strip()
        safe = name
        # En los nombres de fichero "_" separa palabras ("Joan_Puig"): se busca como espacio.
        for m in reversed(Matcher(terms).find(name.replace("_", " "))):
            safe = safe[: m.start] + m.replacement + safe[m.end :]
        safe = re.sub(r'[<>:"/\\|?*]', "_", safe)
        if safe != name:
            self.name_edit.setText(safe)
        if not self._validate_output():
            return
        src, dst, language = self.input_path, self.output_path(), self.language
        guide = self._guide_path(dst)
        self._run_anonymize(src, dst, terms, guide, language)

    def _run_anonymize(self, src, dst, terms, guide, language) -> None:
        self._last_run = (src, dst, terms, guide, language)
        keep = set(self.keep)
        pdf = self.info is not None and self.info.kind == "pdf"
        phases = ["anonymize", "verify"]
        if pdf and dst.suffix == ".txt":
            phases.append("export")

        def task(progress):
            report = anonymize(src, dst, terms, progress, guide, language)
            report.review_text = review.review_text(report.output)
            report.review_words = review.suspicious(report.review_text, keep)
            return report

        estimates = estimate.anonymization(self.info.workload, dst.suffix.lower())
        self._run("progress_anonymizing", phases, task, self._finished, back_to=STEP_SAVE,
                  estimates=estimates)  # fmt: skip

    def review_output(self) -> None:
        """Revisión final: si el usuario marca palabras, se vuelve a anonimizar con ellas."""
        report = self.result_page.report
        if report is None or not report.review_words:
            return
        dialog = ReviewDialog(report.review_text, report.review_words, self.language.code, self)
        if dialog.exec() != ReviewDialog.DialogCode.Accepted or not dialog.selected():
            return
        src, dst, terms, guide, language = self._last_run
        used = {t.replacement for t in terms}
        extra = []
        for word in dialog.selected():
            alias = fill_preset(language.presets[0], used)
            used.add(alias)
            extra.append(Term(word, alias, expand=False, source="REVISIO"))
        self._run_anonymize(src, dst, terms + extra, guide, language)

    # --- Tareas en segundo plano ---------------------------------------------------------

    def _run(self, title_key, phases, fn, on_done, back_to: int, estimates=None) -> None:
        self._step = title_key
        unit = "pages" if self.info is not None and self.info.kind == "pdf" else "images"
        self.progress_page.start(title_key, phases, self.language.code, unit, estimates)
        self._show(self.progress_page)

        def finished(result: object) -> None:
            self._task = None
            self.progress_page.stop()
            on_done(result)

        def failed(error: Exception) -> None:
            self._task = None
            self.progress_page.stop()
            self.go_to(back_to)
            self._failed(error)

        def cancelled() -> None:
            self._task = None
            self.progress_page.stop()
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
            logged = errlog.write(self.log_path, error, self._step)
            if logged:
                message += "\n\n" + tr(lang, "error_logged", path=logged)
        QMessageBox.critical(self, tr(lang, "error_title"), message)

    def show_about(self) -> None:
        AboutDialog(self.language.code, self).exec()

    def show_help(self) -> None:
        HelpDialog(self.language.code, self).exec()

    def _estimate_total(self) -> float:
        if self.info is None:
            return 0.0
        suffix = self.save_page.formats.value() or ".docx"
        return estimate.total(self.info.workload, suffix, ner.is_available())

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
