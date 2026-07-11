# Pokemon Panel for the GUI select pokemon and show its details
# makingGUI with python and Pyside6
from POKEMON import manager
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QLabel,
    QFrame,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QSlider,
    QDial,
)
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QFont,
    QAction,
    QKeySequence,
)
from PySide6.QtCore import (
    Qt,
    QSize,
    QTimer,
)
from typing import Dict, List, Tuple


class SelectionComboBox(QComboBox):
    def __init__(self, placeholder="Select an option", items: Dict[int, str] = {}):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.setPlaceholderText(placeholder)
        self.setCurrentIndex(-1)  # No selection initially
        for key, value in items.items():
            self.addItem(value, key)


class PokemonPanel(QFrame):
    def __init__(self, panel_name):
        super().__init__()
        self.setWindowTitle(f"{panel_name} Panel")
        # window size
        self.setMinimumSize(200, 300)

        # layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel(f"{panel_name} Selection"))
        main_layout.addWidget(
            SelectionComboBox(items=manager.get_selectable_pokemon_map())
        )

        self.setLayout(main_layout)

    # get seleccted pokemon id
    def get_selected_pokemon_id(self) -> int | None:
        """Return the selected Pokemon ID from the combo box."""
        combo_box = self.findChild(SelectionComboBox)
        if combo_box is not None:
            return combo_box.currentData()
        return None
