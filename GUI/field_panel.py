from dataclasses import fields

from pokebase import item
from PySide6.QtCore import (
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtGui import (
    QAction,
    QFont,
    QIcon,
    QKeySequence,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDial,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QStyle,
    QStyleOption,
    QVBoxLayout,
    QWidget,
)

from BATTLE.battle_manager import BattleManager


class FieldPanel(QFrame):
    def __init__(self, battle_manager: BattleManager):
        super().__init__()
        self.battle_manager = battle_manager
        self.setWindowTitle("Field Panel")
        self.setObjectName("field_pannel")
        self.widgets = {}
        main_layout = QVBoxLayout()

        current_field = self.battle_manager.field
        field_class = current_field.__class__

        for field_info in fields(field_class):
            # 💡 現在のインスタンスから「初期値」を取り出して渡す
            current_val = getattr(current_field, field_info.name)

            self.widgets[field_info.name] = self.create_widget_by_type(
                field_info, current_val
            )
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

    def create_widget_by_type(self, field_info, current_val):
        display_name = field_info.name.replace("_", " ").capitalize()

        if field_info.type is str:
            widget = QComboBox()
            widget.setPlaceholderText(display_name)
            widget.addItems(field_info.metadata["choices"])
            # 💡 初期値をセット
            if current_val in field_info.metadata["choices"]:
                widget.setCurrentText(current_val)
            return widget

        elif field_info.type is bool:
            widget = QCheckBox(display_name)
            # 💡 初期値をセット
            widget.setChecked(bool(current_val))
            return widget

        elif field_info.type is int:
            widget = QSpinBox()
            widget.setRange(field_info.metadata["min"], field_info.metadata["max"])
            widget.setPrefix(display_name + ": ")
            # 💡 初期値をセット
            widget.setValue(int(current_val))
            return widget

    def emit_updated_battle_field(self):
        # 💡 インポートしていない BattleField に依存せず、直接属性を上書き！
        current_field = self.battle_manager.field

        for field_info in fields(current_field.__class__):
            widget = self.widgets[field_info.name]

            if isinstance(widget, QComboBox):
                val = widget.currentText()
            elif isinstance(widget, QSpinBox):
                val = widget.value()
            elif isinstance(widget, QCheckBox):
                val = widget.isChecked()

            # 既存のインスタンスの変数を更新！
            setattr(current_field, field_info.name, val)
