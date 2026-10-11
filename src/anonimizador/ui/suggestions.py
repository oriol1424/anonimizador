"""Paso 3: lo que la app ha encontrado y el usuario no había puesto en su lista.

Con documentos largos salen cientos de sugerencias: buscador y filtros por tipo.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from anonimizador.core.lang import Language
from anonimizador.core.matcher import Term
from anonimizador.core.pipeline import Analysis, Suggestion
from anonimizador.core.text import fold
from anonimizador.i18n import tr
from anonimizador.ui import style
from anonimizador.ui.pages import Page
from anonimizador.ui.widgets import FlowLayout, NoticeList, ReplacementCombo, button, label

# Filtros: grupo -> tipos de dato.
GROUPS = {
    "group_people": ("PERSONA",),
    "group_companies": ("EMPRESA",),
    "group_ids": ("DNI", "NIE", "CIF", "NRT", "PASAPORTE", "CASS", "RESIDENCIA"),
    "group_contact": ("TELEFONO", "EMAIL"),
    "group_addresses": ("DIRECCION",),
    "group_other": ("IBAN", "MATRICULA", "PROCEDIMIENTO"),
}
COL_CHECK, COL_TYPE, COL_FOUND, COL_COUNT, COL_ALIAS = range(5)


def _group_of(label_code: str) -> str:
    return next((g for g, labels in GROUPS.items() if label_code in labels), "group_other")


class SuggestionsPage(Page):
    def __init__(self, on_back, on_apply):
        super().__init__()
        self._suggestions: list[Suggestion] = []
        self._used: set[str] = set()
        self._language: Language | None = None
        self._group: str | None = None  # None = todos
        self.combos: list[ReplacementCombo] = []

        self.notices = NoticeList()
        self.body.addWidget(self.notices)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.addAction(style.icon("search", style.SUBTLE, 16),
                              QLineEdit.ActionPosition.LeadingPosition)  # fmt: skip
        self.search.textChanged.connect(lambda _: self._apply_filter())
        search_row.addWidget(self.search, 1)
        self.body.addLayout(search_row)

        self.chips_box = QWidget()
        self.chips = FlowLayout(8)
        self.chips_box.setLayout(self.chips)
        self.body.addWidget(self.chips_box)

        self.table = QTableWidget(0, 5)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setShowGrid(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_FOUND, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_ALIAS, QHeaderView.ResizeMode.Interactive)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.itemChanged.connect(lambda _: self._update_count())
        self.body.addWidget(self.table, 1)
        self.empty = label("", "muted", wrap=True)
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body.addWidget(self.empty, 1)

        self.back_button = button("")
        self.back_button.clicked.connect(on_back)
        self.all_button = button("", "flat")
        self.all_button.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        self.none_button = button("", "flat")
        self.none_button.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
        self.count_label = label("", "small")
        self.apply_button = button("", "primary")
        self.apply_button.clicked.connect(on_apply)
        self.footer.addWidget(self.back_button)
        self.footer.addWidget(self.all_button)
        self.footer.addWidget(self.none_button)
        self.footer.addStretch()
        self.footer.addWidget(self.count_label)
        self.footer.addWidget(self.apply_button)

    # --- Contenido -----------------------------------------------------------------------

    def show_analysis(self, analysis: Analysis, language: Language, used: set[str]) -> None:
        self._suggestions = analysis.suggestions
        self._used = used
        self._language = language
        self._group = None
        self.search.clear()
        self.notices.show_notices(analysis.notices, language)

        self.table.blockSignals(True)
        self.table.setRowCount(len(self._suggestions))
        self.combos = []
        for row, s in enumerate(self._suggestions):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row, COL_CHECK, check)
            for col, text in ((COL_TYPE, ""), (COL_FOUND, " / ".join(s.forms)),
                              (COL_COUNT, str(s.count))):  # fmt: skip
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, col, item)
            combo = ReplacementCombo(language, self._aliases_except)
            combo.setEditText(s.replacement)
            self.table.setCellWidget(row, COL_ALIAS, combo)
            self.combos.append(combo)
        self.table.setColumnWidth(COL_ALIAS, 270)
        self.table.blockSignals(False)
        self.retranslate(language)

    def retranslate(self, language: Language) -> None:
        lang = language.code
        self._language = language
        self.title.setText(tr(lang, "sugg_title"))
        count = len(self._suggestions)
        self.intro.setText(tr(lang, "sugg_found", count=count) if count else "")
        self.intro.setVisible(bool(count))
        self.empty.setText(tr(lang, "sugg_none"))
        self.search.setPlaceholderText(tr(lang, "search"))
        self.table.setHorizontalHeaderLabels(
            [tr(lang, k) for k in ("col_apply", "col_type", "col_found", "col_count")]
            + [tr(lang, "col_replacement")]
        )
        self.table.blockSignals(True)
        for row, s in enumerate(self._suggestions):
            self.table.item(row, COL_TYPE).setText(tr(lang, f"label_{s.label}"))
        self.table.blockSignals(False)
        for combo in self.combos:
            combo.set_language(language)
        self.back_button.setText(tr(lang, "back"))
        self.all_button.setText(tr(lang, "select_all"))
        self.none_button.setText(tr(lang, "select_none"))
        self.apply_button.setText(tr(lang, "apply_continue"))
        self._build_chips(lang)
        self._apply_filter()

    def _build_chips(self, lang: str) -> None:
        while self.chips.count():
            item = self.chips.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        counts: dict[str, int] = {}
        for s in self._suggestions:
            counts[_group_of(s.label)] = counts.get(_group_of(s.label), 0) + 1
        options = [(None, tr(lang, "filter_all"), len(self._suggestions))]
        options += [(g, tr(lang, g), counts[g]) for g in GROUPS if counts.get(g)]
        for group, text, n in options:
            chip = button(f"{text} · {n}", "chip")
            chip.setCheckable(True)
            chip.setChecked(group == self._group)
            chip.clicked.connect(lambda _=False, g=group: self._choose_group(g))
            self.chips.addWidget(chip)
        self.chips_box.setVisible(len(self._suggestions) > 0)

    def _choose_group(self, group: str | None) -> None:
        self._group = group
        lang = self._language.code if self._language else "ca"
        self._build_chips(lang)
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = fold(self.search.text().strip())
        for row, s in enumerate(self._suggestions):
            visible = self._group is None or _group_of(s.label) == self._group
            if visible and query:
                haystack = " ".join(
                    (*s.forms, self.table.item(row, COL_TYPE).text(), self.combos[row].value())
                )
                visible = query in fold(haystack)
            self.table.setRowHidden(row, not visible)
        has_rows = bool(self._suggestions)
        self.table.setVisible(has_rows)
        self.empty.setVisible(not has_rows)
        self.search.setVisible(has_rows)
        for w in (self.all_button, self.none_button, self.count_label):
            w.setVisible(has_rows)
        self._update_count()

    # --- Selección -------------------------------------------------------------------------

    def _aliases_except(self, combo: ReplacementCombo) -> set[str]:
        return self._used | {c.value() for c in self.combos if c is not combo}

    def _set_all(self, state: Qt.CheckState) -> None:
        """Marca o desmarca las filas visibles (las del filtro o la búsqueda actuales)."""
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                self.table.item(row, COL_CHECK).setCheckState(state)
        self.table.blockSignals(False)
        self._update_count()

    def _update_count(self) -> None:
        if self._language is None:
            return
        checked = sum(
            1 for row in range(self.table.rowCount())
            if self.table.item(row, COL_CHECK).checkState() == Qt.CheckState.Checked
        )  # fmt: skip
        self.count_label.setText(
            tr(self._language.code, "marked_count", checked=checked, total=len(self._suggestions))
        )

    def set_checked(self, row: int, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.table.item(row, COL_CHECK).setCheckState(state)

    def selected_terms(self) -> list[Term]:
        terms: list[Term] = []
        for row, s in enumerate(self._suggestions):
            if self.table.item(row, COL_CHECK).checkState() == Qt.CheckState.Checked:
                terms.extend(s.to_terms(self.combos[row].value() or s.replacement))
        return terms
