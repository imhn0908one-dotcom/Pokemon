from typing import Dict
from PySide6.QtWidgets import QComboBox


class SelectionComboBox(QComboBox):
    def __init__(self, placeholder="Select an option", items: Dict[int, str] = {}):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.setPlaceholderText(placeholder)
        self.setCurrentIndex(-1)  # No selection initially
        for key, value in items.items():
            self.addItem(value, key)
