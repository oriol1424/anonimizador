"""Barra lateral: nombre de la app, los 4 pasos, el idioma y el recordatorio de que todo
es local."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from anonimizador.core.lang import LANGUAGES
from anonimizador.i18n import tr
from anonimizador.ui import style
from anonimizador.ui.widgets import Segmented, button, label, set_prop

STEPS = ("step_document", "step_terms", "step_suggestions", "step_save")


class StepButton(QPushButton):
    def __init__(self, number: int):
        super().__init__()
        self.setObjectName("step")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)
        self.number = number
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 0, 10, 0)
        row.setSpacing(12)
        self.marker = QLabel()
        self.text_label = label("", "stepText")
        self.badge = label("", "badge")
        self.badge.hide()
        for w in (self.marker, self.text_label, self.badge):
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(self.marker)
        row.addWidget(self.text_label, 1)
        row.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_state(self, state: str, enabled: bool) -> None:
        """state: "done", "current" o "todo"."""
        self.setEnabled(enabled)
        self.marker.setPixmap(style.step_marker(state, self.number))
        set_prop(self, "current", state == "current")
        set_prop(self.text_label, "current", state == "current")
        set_prop(self.text_label, "enabled", enabled)
        if state == "current":
            self.setAccessibleDescription("current")


class Sidebar(QFrame):
    def __init__(
        self,
        on_step: Callable[[int], None],
        on_language: Callable[[str], None],
        on_keep: Callable[[], None],
        on_about: Callable[[], None] = lambda: None,
    ):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(250)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(24)

        head = QHBoxLayout()
        head.setSpacing(10)
        logo = QLabel()
        logo.setFixedSize(36, 36)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"background: {style.ACCENT}; border-radius: 9px;")
        logo.setPixmap(style.icon_pixmap("logo", "#FFFFFF", 20))
        names = QVBoxLayout()
        names.setSpacing(0)
        self.app_name = label("", "appName")
        self.file_name = label("", "fileName")
        self.file_name.setTextFormat(Qt.TextFormat.PlainText)
        names.addWidget(self.app_name)
        names.addWidget(self.file_name)
        head.addWidget(logo)
        head.addLayout(names, 1)
        layout.addLayout(head)

        steps = QVBoxLayout()
        steps.setSpacing(4)
        self.steps: list[StepButton] = []
        for i in range(len(STEPS)):
            b = StepButton(i + 1)
            b.clicked.connect(lambda _=False, i=i: on_step(i))
            steps.addWidget(b)
            self.steps.append(b)
        layout.addLayout(steps)
        layout.addStretch()

        # Lista de nombres que no se anonimizan nunca (la abogada, el despacho...).
        self.keep_button = button("", "flat")
        self.keep_button.setIcon(style.icon("shield", style.ACCENT, 18))
        self.keep_button.setStyleSheet("text-align: left; padding-left: 10px;")
        self.keep_button.clicked.connect(on_keep)
        layout.addWidget(self.keep_button)
        self.about_button = button("", "flat")
        self.about_button.setIcon(style.icon("info", style.SUBTLE, 18))
        self.about_button.setStyleSheet("text-align: left; padding-left: 10px;")
        self.about_button.clicked.connect(on_about)
        index = layout.indexOf(self.keep_button)
        layout.removeWidget(self.keep_button)
        links = QVBoxLayout()
        links.setSpacing(2)
        links.addWidget(self.keep_button)
        links.addWidget(self.about_button)
        layout.insertLayout(index, links)

        self.language = Segmented([(lang.name, code) for code, lang in LANGUAGES.items()],
                                  on_language)  # fmt: skip
        layout.addWidget(self.language)
        local = QHBoxLayout()
        local.setSpacing(8)
        lock = QLabel()
        lock.setPixmap(style.icon_pixmap("lock", style.SUBTLE, 15))
        self.local_badge = label("", "localBadge")
        local.addWidget(lock)
        local.addWidget(self.local_badge, 1)
        layout.addLayout(local)

    def retranslate(self, lang: str) -> None:
        self.app_name.setText(tr(lang, "app_title"))
        for key, b in zip(STEPS, self.steps, strict=True):
            b.text_label.setText(tr(lang, key))
        self.local_badge.setText(tr(lang, "local_badge"))
        self.about_button.setText(tr(lang, "about_button"))

    def set_file(self, name: str) -> None:
        metrics = self.file_name.fontMetrics()
        self.file_name.setText(metrics.elidedText(name, Qt.TextElideMode.ElideMiddle, 170))
        self.file_name.setToolTip(name)

    def update_steps(self, current: int | None, reachable: list[bool], done: list[bool]) -> None:
        for i, b in enumerate(self.steps):
            state = "current" if i == current else ("done" if done[i] else "todo")
            b.set_state(state, reachable[i])

    def set_keep_count(self, lang: str, count: int) -> None:
        self.keep_button.setText(tr(lang, "keep_button", count=count))

    def set_badge(self, count: int | None) -> None:
        badge = self.steps[2].badge
        badge.setVisible(bool(count))
        badge.setText(str(count or ""))
