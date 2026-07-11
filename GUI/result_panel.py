# Result Panel for the GUI show the result of calculation
# makingGUI with python and Pyside6

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


class ResultPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Result Panel")
        self.setObjectName("result_pannel")

        # window size
        self.setMinimumSize(200, 300)
