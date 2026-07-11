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
    QStyle,
    QDoubleSpinBox,
    QCheckBox,
    QSlider,
    QDial,
    QStyleOption,
)
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QFont,
    QAction,
    QKeySequence,
    QPainter,
)
from PySide6.QtCore import (
    Qt,
    QSize,
    QTimer,
)
from pokebase import item
from FIELD.state import BattleField
from dataclasses import fields


class FieldPanel(QFrame):
    def __init__(self, battle_manager):
        super().__init__()
        self.battle_manager = battle_manager
        self.setWindowTitle("Field Panel")
        self.widgets = {}
        main_layout = QVBoxLayout()

        for field_info in fields(BattleField):
            # widget dict key=name value=widget
            self.widgets[field_info.name] = self.create_widget_by_type(field_info)
            main_layout.addWidget(self.widgets[field_info.name])

        # event connect
        for _, widget in self.widgets.items():
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self.emit_updated_battle_field)
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self.emit_updated_battle_field)
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(self.emit_updated_battle_field)
        self.setLayout(main_layout)

    def create_widget_by_type(self, field_info):
        display_name = field_info.name.replace("_", " ").capitalize()
        if field_info.type is str:
            widget = QComboBox()
            widget.setPlaceholderText(display_name)
            widget.addItems(field_info.metadata["choices"])
            return widget
        elif field_info.type is bool:
            widget = QCheckBox(display_name)
            return widget
        elif field_info.type is int:
            widget = QSpinBox()
            widget.setRange(field_info.metadata["min"], field_info.metadata["max"])
            widget.setPrefix(display_name + ": ")
            return widget

    def emit_updated_battle_field(self):
        state_data = {}
        for field_info in fields(BattleField):
            widget = self.widgets[field_info.name]
            if isinstance(widget, QComboBox):
                state_data[field_info.name] = widget.currentText()
            elif isinstance(widget, QSpinBox):
                state_data[field_info.name] = widget.value()
            elif isinstance(widget, QCheckBox):
                state_data[field_info.name] = widget.isChecked()
        new_battle_field = BattleField(**state_data)
        self.battle_manager.field = new_battle_field
