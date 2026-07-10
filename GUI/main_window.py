# GUI/main_window.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ポケモンAI パーティマネージャー")
        self.resize(1000, 600)

        # メインの横並びレイアウト（ユーザーが比率を変更可能）
        left_frame = QFrame()
        right_frame = QFrame()

        left_frame.setObjectName("sideFrame")
        right_frame.setObjectName("sideFrame")

        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(16)

        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(16)

        party_label = QLabel("パーティ編集エリア")
        party_button = QPushButton("パーティ編集用ダミーボタン")
        damage_label = QLabel("ダメージ計算エリア")
        damage_button = QPushButton("ダメージ計算用ダミーボタン")

        party_label.setObjectName("sectionLabel")
        damage_label.setObjectName("sectionLabel")
        party_button.setObjectName("dummyButton")
        damage_button.setObjectName("dummyButton")

        left_layout.addWidget(party_label)
        left_layout.addWidget(party_button)
        left_layout.addStretch(1)

        right_layout.addWidget(damage_label)
        right_layout.addWidget(damage_button)
        right_layout.addStretch(1)

        splitter = QSplitter(Qt.Horizontal)  # type: ignore
        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([300, 700])

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.addWidget(splitter)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Segoe UI', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
                font-size: 13px;
            }
            QFrame#sideFrame {
                background-color: #252526;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
            QLabel#sectionLabel {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 12px;
            }
            QPushButton#dummyButton {
                min-height: 36px;
                padding: 8px 16px;
                color: #d4d4d4;
                background-color: #0e639c;
                border: 1px solid #0e639c;
                border-radius: 6px;
            }
            QPushButton#dummyButton:hover {
                background-color: #1177c1;
                border-color: #1177c1;
            }
            QPushButton#dummyButton:pressed {
                background-color: #0b4f82;
                border-color: #0b4f82;
            }
            """  # noqa: E501
        )
