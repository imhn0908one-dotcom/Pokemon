# makingGUI with python and Pyside6
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSplitter,
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
import sys
import os
import sqlite3
from typing import Dict, List, Tuple
from datetime import datetime

# pannel import
from POKEMON.instance import PokemonInstance
from POKEMON.manager import learnt_move_names_to_dict
from GUI.pokemon_panel import PokemonPanel
from GUI.result_panel import ResultPanel
from GUI.field_panel import FieldPanel


class MainWindow(QMainWindow):
    """Main window for the Pokemon GUI application.
    This class represents the main window of the application, which contains
    various panels for selecting Pokemon, displaying results, and configuring the field."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window")
        # pannel
        self.left_pannel = PokemonPanel("Attacker")
        self.right_pannel = PokemonPanel("Defender")
        self.result_pannel = ResultPanel()
        self.bottom_pannel = FieldPanel()
        # object name
        self.left_pannel.setObjectName("left_pannel")
        self.right_pannel.setObjectName("right_pannel")
        self.result_pannel.setObjectName("result_pannel")
        self.bottom_pannel.setObjectName("bottom_pannel")

        # window size
        self.setMinimumSize(1500, 1000)

        # layout by splitter
        self.sep1 = QSplitter(Qt.Orientation.Vertical)
        self.sep1.addWidget(self.result_pannel)
        self.sep1.addWidget(self.bottom_pannel)

        # main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.left_pannel)
        main_layout.addWidget(self.sep1)
        main_layout.addWidget(self.right_pannel)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # main widget
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # style sheet
        self.load_stylesheet("GUI/style.qss")

    def load_stylesheet(self, stylesheet_path: str):
        """Load a stylesheet from a file and apply it to the main window."""
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"Stylesheet file not found: {stylesheet_path}")
