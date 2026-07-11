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


class FieldPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Field Panel")
