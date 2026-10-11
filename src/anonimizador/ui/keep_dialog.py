"""Diálogo para editar la lista de nombres y datos que no se anonimizan nunca."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from anonimizador.core import keep_list
from anonimizador.i18n import tr
from anonimizador.ui.widgets import button, label


class KeepDialog(QDialog):
    def __init__(self, items: list[str], lang: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr(lang, "keep_title"))
        self.resize(620, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(12)
        layout.addWidget(label(tr(lang, "keep_title"), "h2"))
        layout.addWidget(label(tr(lang, "keep_intro"), "muted", wrap=True))

        self.table = QTableWidget(0, 1)
        self.table.setHorizontalHeaderLabels([tr(lang, "keep_col")])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        for item in items:
            self.add_row(item)
        if not items:
            self.add_row()
        layout.addWidget(self.table, 1)

        row = QHBoxLayout()
        add = button(tr(lang, "add_row"))
        add.clicked.connect(lambda: self.add_row(edit=True))
        remove = button(tr(lang, "remove_row"), "flat")
        remove.clicked.connect(self.remove_selected)
        row.addWidget(add)
        row.addWidget(remove)
        row.addStretch()
        cancel = button(tr(lang, "cancel"))
        cancel.clicked.connect(self.reject)
        save = button(tr(lang, "save_button"), "primary")
        save.setDefault(True)
        save.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)

    def add_row(self, text: str = "", edit: bool = False) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(text))
        if edit:
            self.table.setCurrentCell(row, 0)
            self.table.editItem(self.table.item(row, 0))

    def remove_selected(self) -> None:
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)

    def items(self) -> list[str]:
        texts = (self.table.item(r, 0).text() for r in range(self.table.rowCount())
                 if self.table.item(r, 0))  # fmt: skip
        return keep_list.clean(texts)
