"""Componentes compartidos por las pantallas de la ventana."""

import re
from collections.abc import Callable

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from anonimizador.core.lang import Language, fill_preset
from anonimizador.core.pipeline import Notice
from anonimizador.ui import style


class ReplacementCombo(QComboBox):
    """Desplegable editable de "Substituir per".

    Ofrece las opciones del idioma ("[CLIENT_n]"...) y, al elegir una, pone el primer
    número libre ("[CLIENT_2]" si ya existe "[CLIENT_1]"). También se puede escribir.
    """

    def __init__(
        self,
        language: Language,
        used_aliases: Callable[["ReplacementCombo"], set[str]],
        own: str | None = None,
    ):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._used_aliases = used_aliases
        # Sugerencias: el tipo propio de la fila ("[DNI_{n}]") va el primero de la lista.
        self._own = re.sub(r"_\d+\]$", "_{n}]", own) if own else None
        self.set_language(language)
        self.activated.connect(self._on_activated)

    def set_language(self, language: Language) -> None:
        current = self.currentText()
        self.blockSignals(True)
        self.clear()
        templates = list(language.presets)
        if self._own and "{n}" in self._own and self._own not in templates:
            templates.insert(0, self._own)
        for template in templates:
            self.addItem(template.replace("{n}", "n"), template)
        self.setCurrentIndex(-1)
        self.setEditText(current)
        self.blockSignals(False)

    def _on_activated(self, index: int) -> None:
        template = self.itemData(index)
        if template:
            self.setEditText(fill_preset(template, self._used_aliases(self)))

    def choose(self, template: str) -> None:
        self.setEditText(fill_preset(template, self._used_aliases(self)))

    def value(self) -> str:
        return self.currentText().strip()

    def paintEvent(self, event) -> None:  # noqa: N802 (API de Qt)
        # La hoja de estilo quita la flecha nativa (cada sistema la dibuja distinta):
        # se dibuja aquí para que se vea que es un desplegable.
        super().paintEvent(event)
        size = 16
        rect = self.rect().adjusted(0, 0, -12, 0)
        point = QPoint(rect.right() - size, rect.center().y() - size // 2 + 1)
        QPainter(self).drawPixmap(point, style.icon_pixmap("chevron", style.ACCENT, size))


class FlowLayout(QLayout):
    """Coloca los elementos en fila y baja de línea cuando no caben (filtros)."""

    def __init__(self, spacing: int = 8):
        super().__init__()
        self._items = []
        self._spacing = spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item) -> None:  # noqa: N802 (API de Qt)
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):  # noqa: N802 (API de Qt)
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index: int):  # noqa: N802 (API de Qt)
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self) -> Qt.Orientation:  # noqa: N802 (API de Qt)
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:  # noqa: N802 (API de Qt)
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802 (API de Qt)
        return self._place(QRect(0, 0, width, 0), move=False)

    def setGeometry(self, rect: QRect) -> None:  # noqa: N802 (API de Qt)
        super().setGeometry(rect)
        self._place(rect, move=True)

    def sizeHint(self) -> QSize:  # noqa: N802 (API de Qt)
        return self.minimumSize()

    def minimumSize(self) -> QSize:  # noqa: N802 (API de Qt)
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        return size

    def _place(self, rect: QRect, move: bool) -> int:
        x, y, line = rect.x(), rect.y(), 0
        for item in self._items:
            hint = item.sizeHint()
            if x + hint.width() > rect.right() and line > 0:
                x, y, line = rect.x(), y + line + self._spacing, 0
            if move:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + self._spacing
            line = max(line, hint.height())
        return y + line - rect.y()


def label(text: str = "", name: str | None = None, wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    if name:
        widget.setObjectName(name)
    widget.setWordWrap(wrap)
    return widget


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(10)
    return frame, layout


def button(text: str = "", name: str | None = None) -> QPushButton:
    widget = QPushButton(text)
    if name:
        widget.setObjectName(name)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    return widget


def set_prop(widget: QWidget, name: str, value: object) -> None:
    """Cambia una propiedad usada por la hoja de estilos y repinta."""
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class Segmented(QWidget):
    """Grupo de botones excluyentes (p. ej. Català | Castellano)."""

    def __init__(self, options: list[tuple[str, object]], on_change: Callable[[object], None]):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.group = QButtonGroup(self)
        self.buttons: dict[object, QPushButton] = {}
        for text, value in options:
            b = button(text, "segment")
            b.setCheckable(True)
            self.group.addButton(b)
            layout.addWidget(b)
            self.buttons[value] = b
            b.clicked.connect(lambda _=False, v=value: on_change(v))

    def set_value(self, value: object) -> None:
        if value in self.buttons:
            self.buttons[value].setChecked(True)

    def value(self) -> object:
        return next((v for v, b in self.buttons.items() if b.isChecked()), None)

    def set_text(self, value: object, text: str) -> None:
        self.buttons[value].setText(text)


class NoticeList(QWidget):
    """Avisos del núcleo; los graves (datos sin borrar, páginas sin procesar) primero y en
    rojo."""

    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

    def show_notices(self, notices: list[Notice], language: Language) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for notice in sorted(notices, key=lambda n: not n.is_serious):
            level = "serious" if notice.is_serious else "warning"
            frame = QFrame()
            frame.setObjectName("notice")
            frame.setProperty("level", level)
            row = QHBoxLayout(frame)
            row.setContentsMargins(12, 10, 12, 10)
            row.setSpacing(10)
            mark = QLabel()
            color = style.DANGER if level == "serious" else style.WARNING
            mark.setPixmap(style.icon_pixmap("alert", color, 18))
            mark.setAlignment(Qt.AlignmentFlag.AlignTop)
            text = label(notice.message(language), "noticeText", wrap=True)
            text.setProperty("level", level)
            text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(mark)
            row.addWidget(text, 1)
            self._layout.addWidget(frame)
        self.setVisible(bool(notices))
