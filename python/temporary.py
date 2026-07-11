from Pyside6.QtGui import QPainter, QBrush, QColor, QPen, QPaintEvent, QFont, QIcon


def paintEvent(self, event: QPaintEvent) -> None:
    painter = QPainter(self)
    hints = painter.renderHints()
    if QPainter.Antialiasing in hints:
        painter.setRenderHint(QPainter.Antialiasing)
    r = self.rect()
    radius = 10
    # rest of the code
