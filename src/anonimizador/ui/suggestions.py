"""Diálogo con lo que la app ha encontrado y el usuario no había puesto en su lista."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from anonimizador.core.lang import Language
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import Analysis
from anonimizador.i18n import tr
from anonimizador.ui.widgets import ReplacementCombo


class SuggestionsDialog(QDialog):
    def __init__(self, analysis: Analysis, language: Language, used_aliases: set[str], parent=None):
        super().__init__(parent)
        lang = language.code
        self._suggestions = analysis.suggestions
        self._used = used_aliases
        self.setWindowTitle(tr(lang, "sugg_title"))
        self.resize(760, 480)

        layout = QVBoxLayout(self)
        if analysis.notices:
            notices = QLabel(
                f"<b>{tr(lang, 'warnings')}:</b><br>"
                + "<br>".join(f"• {n.message(language)}" for n in analysis.notices)
            )
            notices.setWordWrap(True)
            notices.setObjectName("notices")
            layout.addWidget(notices)

        self.table = QTableWidget(len(self._suggestions), 5)
        self.table.setHorizontalHeaderLabels(
            [tr(lang, k) for k in ("col_apply", "col_type", "col_found", "col_count")]
            + [tr(lang, "col_replacement")]
        )
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.combos: list[ReplacementCombo] = []
        for row, s in enumerate(self._suggestions):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row, 0, check)
            for col, text in ((1, tr(lang, f"label_{s.label}")), (2, " / ".join(s.forms)),
                              (3, str(s.count))):  # fmt: skip
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, col, item)
            combo = ReplacementCombo(language, self._aliases_except)
            combo.setEditText(s.replacement)
            self.table.setCellWidget(row, 4, combo)
            self.combos.append(combo)

        if self._suggestions:
            layout.addWidget(QLabel(tr(lang, "sugg_intro"), wordWrap=True))
            layout.addWidget(self.table)
        else:
            self.table.hide()

        buttons = QHBoxLayout()
        if self._suggestions:
            all_btn = QPushButton(tr(lang, "select_all"))
            none_btn = QPushButton(tr(lang, "select_none"))
            all_btn.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
            none_btn.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
            buttons.addWidget(all_btn)
            buttons.addWidget(none_btn)
        buttons.addStretch()
        cancel = QPushButton(tr(lang, "cancel"))
        cancel.clicked.connect(self.reject)
        self.apply_button = QPushButton(tr(lang, "apply_and_save"))
        self.apply_button.setDefault(True)
        self.apply_button.setObjectName("primary")
        self.apply_button.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(self.apply_button)
        layout.addLayout(buttons)

    def _aliases_except(self, combo: ReplacementCombo) -> set[str]:
        return self._used | {c.value() for c in self.combos if c is not combo}

    def _set_all(self, state: Qt.CheckState) -> None:
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(state)

    def selected_terms(self) -> list[Term]:
        terms: list[Term] = []
        for row, s in enumerate(self._suggestions):
            if self.table.item(row, 0).checkState() == Qt.CheckState.Checked:
                terms.extend(s.to_terms(self.combos[row].value() or s.replacement))
        return terms
