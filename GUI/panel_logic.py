from typing import Dict
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import QSize


class SelectionComboBox(QComboBox):
    def __init__(
        self,
        placeholder="Select an option",
        items: Dict[int, str] = {},
        objectName="pokemon_selection",
    ):
        super().__init__()
        self.setEditable(True)
        self.setObjectName(objectName)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setIconSize(QSize(32, 32))
        self.setPlaceholderText(placeholder)
        self.setCurrentIndex(-1)  # No selection initially
        for key, value in items.items():
            image_path = f"IMAGES/{self.objectName()}/{value}.png"
            print(image_path)
            icon = QIcon(image_path)
            self.addItem(icon, value, key)
