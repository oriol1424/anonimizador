"""Componentes compartidos por la ventana principal y el diálogo de sugerencias."""

from collections.abc import Callable

from PySide6.QtWidgets import QComboBox

from anonimizador.core.lang import Language, fill_preset


class ReplacementCombo(QComboBox):
    """Desplegable editable de "Substituir per".

    Ofrece las opciones del idioma ("[CLIENT_n]"...) y, al elegir una, pone el primer
    número libre ("[CLIENT_2]" si ya existe "[CLIENT_1]"). También se puede escribir.
    """

    def __init__(self, language: Language, used_aliases: Callable[["ReplacementCombo"], set[str]]):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._used_aliases = used_aliases
        self.set_language(language)
        self.activated.connect(self._on_activated)

    def set_language(self, language: Language) -> None:
        current = self.currentText()
        self.blockSignals(True)
        self.clear()
        for template in language.presets:
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
