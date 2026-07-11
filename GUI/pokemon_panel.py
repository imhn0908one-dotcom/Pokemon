# Pokemon Panel for the GUI select pokemon and show its details
# makingGUI with python and Pyside6
from POKEMON import manager, instance, factory

from dataclasses import dataclass, fields
from typing import Dict
from FIELD.state import BattleField
from .field_panel import FieldPanel
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
from typing import List, Tuple
from GUI import panel_logic
from GUI import field_panel


class PokemonPanel(QFrame):
    def __init__(self, panel_name, battle_manager):
        super().__init__()
        self.setWindowTitle(f"{panel_name} Panel")
        self.battle_manager = battle_manager
        self.instance_atk_or_def = panel_name
        # window size
        self.setMinimumSize(200, 300)
        self.side_state_widget = {}
        # layout
        self.field_selection_layout = QVBoxLayout()
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel(f"{panel_name} Selection"))
        self.pokemon_combo = panel_logic.SelectionComboBox(
            items=manager.get_selectable_pokemon_map(),
            placeholder="Select a Pokemon",
            objectName="pokemon_selection",
        )
        self.pokemon_combo.currentIndexChanged.connect(
            self.emit_updated_pokemon_instance
        )
        main_layout.addWidget(self.pokemon_combo)
        print(self.styleSheet())
        self.setLayout(main_layout)

    # if pokemon is selected, emit pokemon instance
    def emit_updated_pokemon_instance(self):
        id = self.pokemon_combo.currentData()
        maked_instance = factory.create_pokemon_by_id(id)
        if self.instance_atk_or_def == "attacker":
            self.battle_manager.set_attacker(maked_instance)
        elif self.instance_atk_or_def == "defender":
            self.battle_manager.set_defender(maked_instance)
