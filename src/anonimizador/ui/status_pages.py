"""Pantallas de progreso (fases, tiempo restante, Cancel·la) y de resultado."""

import math
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout

from anonimizador.core.lang import Language
from anonimizador.core.pipeline import Report
from anonimizador.i18n import tr
from anonimizador.ui import style
from anonimizador.ui.pages import NoticeLabel, Page
from anonimizador.ui.widgets import NoticeList, button, card, label, set_prop

PAGE_PHASES = {"read", "anonymize", "verify", "export"}  # se cuentan en páginas
ETA_AFTER_SECONDS = 3.0  # antes, la estimación no es fiable
STILL_WORKING_AFTER = 40  # s sin noticias: se avisa de que sigue trabajando


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
    """Progreso global (%), tiempo restante, tiempo transcurrido y fases.

    El porcentaje combina las fases según su duración estimada (`core/estimate.py`); el
    tiempo restante se corrige con la velocidad real de este ordenador. Un reloj que avanza
    cada segundo deja claro que la app no se ha colgado, y si una parte tarda mucho sin dar
    noticias se dice que sigue trabajando.
    """

    def __init__(self, on_cancel: Callable[[], None]):
        super().__init__()
        self._lang = "ca"
        self._unit = "pages"
        self._phases: list[str] = []
        self._estimates: dict[str, float] = {}
        self._fraction: dict[str, float] = {}
        self._events: set[str] = set()  # fases que ya han dado noticias
        self._rows: list[_PhaseRow] = []
        self._current = 0
        self._detail = ""
        self._started = self._phase_started = self._last_event = time.monotonic()
        self._title_key = "progress_analyzing"

        box, layout = card()
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        top = QHBoxLayout()
        self.percent = label("", "h1")
        status = QVBoxLayout()
        status.setSpacing(2)
        self.eta = label("", "muted")
        self.elapsed = label("", "small")
        status.addWidget(self.eta)
        status.addWidget(self.elapsed)
        top.addWidget(self.percent)
        top.addSpacing(16)
        top.addLayout(status, 1)
        self.activity = label("", "small")
        top.addWidget(self.activity, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(top)
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        layout.addWidget(self.bar)
        self.position = label("", "small")
        layout.addWidget(self.position)
        self.phase_box = QVBoxLayout()
        self.phase_box.setSpacing(4)
        layout.addLayout(self.phase_box)
        self.body.addWidget(box)

        self.still_working = NoticeLabel()
        self.body.addWidget(self.still_working)
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

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

    # --- Ciclo de una tarea ---------------------------------------------------------------

    def start(self, title_key: str, phases: list[str], lang: str, unit: str = "pages",
              estimates: dict[str, float] | None = None) -> None:  # fmt: skip
        """`unit`: qué se cuenta en las fases por elementos ("pages" en PDF, "images" en
        Word). `estimates`: segundos previstos por fase."""
        self._lang, self._unit, self._title_key = lang, unit, title_key
        self._phases = phases
        self._estimates = {p: (estimates or {}).get(p, 1.0) for p in phases}
        self._fraction = dict.fromkeys(phases, 0.0)
        self._events = set()
        self._current = 0
        self._detail = ""
        self._started = self._phase_started = self._last_event = time.monotonic()
        for row in self._rows:
            self.phase_box.removeWidget(row)
            row.deleteLater()
        self._rows = [_PhaseRow(code) for code in phases]
        for row in self._rows:
            self.phase_box.addWidget(row)
        self.cancel_button.setEnabled(True)
        self.still_working.hide()
        self.retranslate(lang)
        self._refresh()
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()

    def update_progress(self, phase: str, done: int, total: int) -> None:
        if phase not in self._phases:
            return
        index = self._phases.index(phase)
        now = time.monotonic()
        if index != self._current:
            for earlier in self._phases[:index]:
                self._fraction[earlier] = 1.0
            self._current = index
            self._phase_started = now
        self._events.add(phase)
        self._last_event = now
        self._fraction[phase] = done / total if total else 0.0
        if phase in PAGE_PHASES:
            self._detail = tr(self._lang, f"phase_{self._unit}", done=done, total=total)
        else:
            self._detail = tr(
                self._lang, "phase_percent", percent=round(100 * done / max(total, 1))
            )
        self.still_working.hide()
        self._refresh()

    # --- Cálculos ---------------------------------------------------------------------------

    def overall(self) -> float:
        """Fracción total hecha (0-1), ponderando cada fase por su duración prevista."""
        total = sum(self._estimates.values()) or 1.0
        done = 0.0
        now = time.monotonic()
        for i, phase in enumerate(self._phases):
            fraction = self._fraction[phase]
            if i == self._current and phase not in self._events:
                # Fase sin noticias (p. ej. el texto de un Word): avanza según lo previsto,
                # sin pasar del 90 % hasta que termine.
                expected = self._estimates[phase] or 1.0
                fraction = max(fraction, min(0.9, (now - self._phase_started) / expected))
            done += self._estimates[phase] * fraction
        return min(done / total, 0.999)

    def remaining_seconds(self) -> float | None:
        elapsed = time.monotonic() - self._started
        overall = self.overall()
        if elapsed < ETA_AFTER_SECONDS or overall < 0.02:
            return None
        return elapsed * (1 - overall) / overall

    # --- Pantalla ---------------------------------------------------------------------------

    def _tick(self) -> None:
        self._refresh()
        quiet = time.monotonic() - self._last_event
        if quiet >= STILL_WORKING_AFTER:
            self.still_working.setText(tr(self._lang, "still_working"))
            self.still_working.show()

    def _refresh(self) -> None:
        lang = self._lang
        overall = self.overall()
        self.bar.setValue(int(overall * 1000))
        self.percent.setText(f"{int(overall * 100)} %")
        remaining = self.remaining_seconds()
        if remaining is None:
            estimate = sum(self._estimates.values())
            self.eta.setText(tr(lang, "eta_estimated", time=duration(lang, estimate)))
        else:
            self.eta.setText(tr(lang, "eta", time=duration(lang, remaining)))
        elapsed = int(time.monotonic() - self._started)
        self.elapsed.setText(tr(lang, "elapsed", time=f"{elapsed // 60}:{elapsed % 60:02d}"))
        dots = "●" * (elapsed % 3 + 1) + "○" * (2 - elapsed % 3)
        self.activity.setText(f"{tr(lang, 'working_now')} {dots}")
        self.position.setText(self._detail[:1].upper() + self._detail[1:])
        self._paint_rows()

    def retranslate(self, lang: str) -> None:
        self._lang = lang
        self.title.setText(tr(lang, self._title_key))
        self.intro.setText("")
        self.intro.hide()
        self.note.setText(tr(lang, "keep_awake_note"))
        if self.cancel_button.isEnabled():
            self.cancel_button.setText(tr(lang, "cancel"))
        if self._phases:
            self._refresh()

    def _paint_rows(self) -> None:
        for i, row in enumerate(self._rows):
            row.name.setText(tr(self._lang, f"phase_{row.code}"))
            if i < self._current:
                row.set_state("done", tr(self._lang, "phase_done"))
            elif i == self._current:
                row.set_state("current", self._detail)
            else:
                row.set_state("pending", tr(self._lang, "phase_pending"))

    def _cancel(self) -> None:
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText(tr(self._lang, "cancelling"))
        self._on_cancel()


def duration(lang: str, seconds: float) -> str:
    """ "menys d'un minut", "uns 3 min"."""
    if seconds < 60:
        return tr(lang, "eta_less_minute")
    return tr(lang, "eta_minutes", n=math.ceil(seconds / 60))


class ResultPage(Page):
    def __init__(self, on_open_folder, on_open_file, on_new, on_review=lambda: None):
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

        # Revisión final: palabras con mayúscula que siguen en el documento.
        self.review_box, review_layout = card()
        review_row = QHBoxLayout()
        review_row.setSpacing(14)
        self.review_label = label("", "muted", wrap=True)
        self.review_button = button("", "primary")
        self.review_button.clicked.connect(on_review)
        review_head = QVBoxLayout()
        review_head.setSpacing(4)
        self.review_title = label("", "h2")
        review_head.addWidget(self.review_title)
        review_head.addWidget(self.review_label)
        review_row.addLayout(review_head, 1)
        review_row.addWidget(self.review_button)
        review_layout.addLayout(review_row)
        self.body.addWidget(self.review_box)

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
        count = len(report.review_words)
        self.review_title.setText(tr(lang, "review_title"))
        self.review_label.setText(
            tr(lang, "review_found", count=count) if count else tr(lang, "review_none")
        )
        self.review_button.setText(tr(lang, "review_button"))
        self.review_button.setVisible(bool(count))
