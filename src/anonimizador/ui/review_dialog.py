"""Revisión final: el texto anonimizado con las palabras sospechosas resaltadas."""

import html
import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QTextBrowser,
    QVBoxLayout,
)

from anonimizador.i18n import tr
from anonimizador.ui import style
from anonimizador.ui.widgets import button, label

MAX_CHARS = 300_000  # más texto haría lenta la vista; las palabras se cuentan igual
HIGHLIGHT = "#FFE58A"


def highlighted_html(text: str, words: list[str]) -> str:
    text = text[:MAX_CHARS]
    if not words:
        return f"<pre style='white-space: pre-wrap'>{html.escape(text)}</pre>"
    pattern = re.compile(
        r"(?<![\w·])(" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
        + r")(?![\w·])"
    )  # fmt: skip
    parts, last = [], 0
    for m in pattern.finditer(text):
        parts.append(html.escape(text[last : m.start()]))
        parts.append(f"<span style='background:{HIGHLIGHT}'>{html.escape(m.group())}</span>")
        last = m.end()
    parts.append(html.escape(text[last:]))
    body = "".join(parts)
    return (
        f"<div style='white-space: pre-wrap; font-size: 10.5pt; color: {style.TEXT}'>{body}</div>"
    )


class ReviewDialog(QDialog):
    def __init__(self, text: str, words: list[tuple[str, int]], lang: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr(lang, "review_title"))
        self.resize(980, 640)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(12)
        layout.addWidget(label(tr(lang, "review_title"), "h2"))
        layout.addWidget(label(tr(lang, "review_intro"), "muted", wrap=True))

        row = QHBoxLayout()
        row.setSpacing(14)
        self.viewer = QTextBrowser()
        self.viewer.setHtml(highlighted_html(text, [w for w, _ in words]))
        row.addWidget(self.viewer, 3)
        self.words = QListWidget()
        for word, count in words:
            item = QListWidgetItem(f"{word}  ({count})")
            item.setData(Qt.ItemDataRole.UserRole, word)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.words.addItem(item)
        self.words.currentItemChanged.connect(self._show_word)
        self.words.itemChanged.connect(lambda _: self._update_button())
        row.addWidget(self.words, 1)
        layout.addLayout(row, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close = button(tr(lang, "close"))
        close.clicked.connect(self.reject)
        self.apply_button = button(tr(lang, "review_apply"), "primary")
        self.apply_button.clicked.connect(self.accept)
        buttons.addWidget(close)
        buttons.addWidget(self.apply_button)
        layout.addLayout(buttons)
        self._update_button()

    def _show_word(self, item: QListWidgetItem | None) -> None:
        """Salta a la siguiente aparición de la palabra elegida."""
        if item is None:
            return
        word = item.data(Qt.ItemDataRole.UserRole)
        flags = QTextDocument.FindFlag.FindWholeWords | QTextDocument.FindFlag.FindCaseSensitively
        if not self.viewer.find(word, flags):
            self.viewer.moveCursor(self.viewer.textCursor().MoveOperation.Start)
            self.viewer.find(word, flags)

    def _update_button(self) -> None:
        self.apply_button.setEnabled(bool(self.selected()))

    def selected(self) -> list[str]:
        return [
            self.words.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.words.count())
            if self.words.item(i).checkState() == Qt.CheckState.Checked
        ]
