"""Pantallas de progreso (fases, tiempo restante, Cancel·la) y de resultado."""

import math
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout

from anonimizador.core.lang import Language
from anonimizador.core.pipeline import Report
from anonimizador.i18n import tr
from anonimizador.ui import style
from anonimizador.ui.pages import Page
from anonimizador.ui.widgets import NoticeList, button, card, label, set_prop

PAGE_PHASES = {"read", "anonymize", "verify", "export"}  # se cuentan en páginas
ETA_AFTER_SECONDS = 3.0  # antes, la estimación no es fiable


class _PhaseRow(QFrame):
    def __init__(self, code: str):
        super().__init__()
        self.setObjectName("phase")
        self.code = code
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(14)
        self.marker = QLabel()
        self.name = label("", "phaseName")
        self.detail = label("", "small")
        row.addWidget(self.marker)
        row.addWidget(self.name, 1)
        row.addWidget(self.detail)

    def set_state(self, state: str, detail: str) -> None:
        self.marker.setPixmap(style.phase_marker(state))
        set_prop(self, "current", state == "current")
        set_prop(self.name, "pending", state == "pending")
        self.detail.setText(detail)


class ProgressPage(Page):
    def __init__(self, on_cancel: Callable[[], None]):
        super().__init__()
        self._lang = "ca"
        self._phases: list[str] = []
        self._rows: list[_PhaseRow] = []
        self._current = 0
        self._phase_started = time.monotonic()

        box, layout = card()
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)
        top = QHBoxLayout()
        self.position = label("", "small")
        self.percent = label("", "small")
        top.addWidget(self.position)
        top.addStretch()
        top.addWidget(self.percent)
        layout.addLayout(top)
        self.bar = QProgressBar()
        layout.addWidget(self.bar)
        self.eta = label("", "muted")
        layout.addWidget(self.eta)
        self.phase_box = QVBoxLayout()
        self.phase_box.setSpacing(4)
        layout.addLayout(self.phase_box)
        self.body.addWidget(box)
        self.body.addStretch()

        note = QHBoxLayout()
        note.setSpacing(8)
        clock = QLabel()
        clock.setPixmap(style.icon_pixmap("clock", style.SUBTLE, 16))
        self.note = label("", "small", wrap=True)
        note.addWidget(clock)
        note.addWidget(self.note, 1)
        self.body.addLayout(note)

        self.footer.addStretch()
        self.cancel_button = button("")
        self.cancel_button.clicked.connect(self._cancel)
        self._on_cancel = on_cancel
        self.footer.addWidget(self.cancel_button)

    def start(self, title_key: str, phases: list[str], lang: str) -> None:
        self._lang = lang
        self._title_key = title_key
        self._phases = phases
        self._current = 0
        self._phase_started = time.monotonic()
        for row in self._rows:
            self.phase_box.removeWidget(row)
            row.deleteLater()
        self._rows = [_PhaseRow(code) for code in phases]
        for row in self._rows:
            self.phase_box.addWidget(row)
        self.cancel_button.setEnabled(True)
        self.bar.setRange(0, 0)  # en marcha, sin total todavía
        self.position.setText("")
        self.percent.setText("")
        self.retranslate(lang)

    def retranslate(self, lang: str) -> None:
        self._lang = lang
        self.title.setText(tr(lang, getattr(self, "_title_key", "progress_analyzing")))
        self.intro.setText("")
        self.intro.hide()
        self.note.setText(tr(lang, "keep_awake_note"))
        if self.cancel_button.isEnabled():
            self.cancel_button.setText(tr(lang, "cancel"))
        self._paint_rows("")
        if not self.eta.text():
            self.eta.setText(tr(lang, "eta_unknown"))

    def _paint_rows(self, current_detail: str) -> None:
        for i, row in enumerate(self._rows):
            row.name.setText(tr(self._lang, f"phase_{row.code}"))
            if i < self._current:
                row.set_state("done", tr(self._lang, "phase_done"))
            elif i == self._current:
                row.set_state("current", current_detail)
            else:
                row.set_state("pending", tr(self._lang, "phase_pending"))

    def update_progress(self, phase: str, done: int, total: int) -> None:
        if phase not in self._phases:
            return
        index = self._phases.index(phase)
        if index != self._current:
            self._current = index
            self._phase_started = time.monotonic()
        lang = self._lang
        self.bar.setRange(0, max(total, 1))
        self.bar.setValue(done)
        percent = round(100 * done / total) if total else 0
        self.percent.setText(tr(lang, "phase_percent", percent=percent))
        if phase in PAGE_PHASES:
            detail = tr(lang, "phase_pages", done=done, total=total)
        else:
            detail = tr(lang, "phase_percent", percent=percent)
        self.position.setText(detail[:1].upper() + detail[1:])
        self._paint_rows(detail)
        self.eta.setText(self._eta_text(done, total))

    def _eta_text(self, done: int, total: int) -> str:
        elapsed = time.monotonic() - self._phase_started
        if done < 1 or elapsed < ETA_AFTER_SECONDS:
            return tr(self._lang, "eta_unknown")
        remaining = elapsed / done * (total - done)
        if remaining < 60:
            when = tr(self._lang, "eta_less_minute")
        else:
            when = tr(self._lang, "eta_minutes", n=math.ceil(remaining / 60))
        return tr(self._lang, "eta", time=when)

    def _cancel(self) -> None:
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText(tr(self._lang, "cancelling"))
        self._on_cancel()


class ResultPage(Page):
    def __init__(self, on_open_folder, on_open_file, on_new):
        super().__init__()
        box, layout = card()
        layout.setContentsMargins(24, 22, 24, 22)
        head = QHBoxLayout()
        head.setSpacing(14)
        self.mark = QLabel()
        self.headline = label("", "h2", wrap=True)
        head.addWidget(self.mark)
        head.addWidget(self.headline, 1)
        layout.addLayout(head)
        self.summary = label("", "muted", wrap=True)
        self.path = label("", None, wrap=True)
        self.path.setTextFormat(Qt.TextFormat.PlainText)
        self.path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.guide = label("", "small", wrap=True)
        self.guide.setTextFormat(Qt.TextFormat.PlainText)
        self.guide.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        for w in (self.summary, self.path, self.guide):
            layout.addWidget(w)
        buttons = QHBoxLayout()
        self.open_file_button = button("")
        self.open_file_button.clicked.connect(on_open_file)
        self.open_folder_button = button("")
        self.open_folder_button.clicked.connect(on_open_folder)
        buttons.addWidget(self.open_file_button)
        buttons.addWidget(self.open_folder_button)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.body.addWidget(box)
        self.notices = NoticeList()
        self.body.addWidget(self.notices)
        self.body.addStretch()

        self.footer.addStretch()
        self.new_button = button("", "primary")
        self.new_button.clicked.connect(on_new)
        self.footer.addWidget(self.new_button)
        self.report: Report | None = None

    def show_report(self, report: Report, language: Language) -> None:
        self.report = report
        self.notices.show_notices(report.notices, language)
        self.retranslate(language)

    def retranslate(self, language: Language) -> None:
        lang = language.code
        self.open_file_button.setText(tr(lang, "open_file"))
        self.open_folder_button.setText(tr(lang, "open_folder"))
        self.new_button.setText(tr(lang, "new_document"))
        report = self.report
        if report is None:
            return
        serious = any(n.is_serious for n in report.notices)
        if serious:
            key, color, icon = "result_serious", style.DANGER, "alert"
        elif report.notices:
            key, color, icon = "result_warn", style.WARNING, "alert"
        else:
            key, color, icon = "result_ok", style.SUCCESS, "check"
        self.title.setText(tr(lang, "done_title"))
        self.intro.hide()
        self.mark.setPixmap(style.icon_pixmap(icon, color, 32, 2.4))
        self.headline.setText(tr(lang, key))
        self.headline.setStyleSheet(f"color: {color};")
        self.summary.setText(tr(lang, "result_summary", total=report.total))
        self.path.setText(str(report.output))
        self.guide.setVisible(report.guide is not None)
        if report.guide is not None:
            self.guide.setText(tr(lang, "guide_saved", path=Path(report.guide)))
        self.notices.show_notices(report.notices, language)
