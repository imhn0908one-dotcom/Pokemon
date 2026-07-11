# GUI/main_window.py

from POKEMON.factory import create_pokemon_by_id
from POKEMON.manager import get_selectable_pokemon_map
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QSpacerItem,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


# Run from the project root or GUI folder; ensure the root is on sys.path.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class MainWindow(QMainWindow):
    """メイン GUI ウィンドウ。

    - 左サイド: ポケモンの選択とインスタンス生成操作を行うパネル
    - 右サイド: 生成された `PokemonInstance` の情報を表示するパネル
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ポケモンAI パーティマネージャー")
        self.resize(1000, 620)

        # DB から取得した「選択可能なポケモン一覧」。
        # key が ID、value が名前の辞書となる。
        self.pokemon_map = self._load_pokemon_list()

        # 左右に分割されたパネルを用意する。
        # 左側は選択操作、右側は表示専用として使う。
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

        party_label = QLabel("ポケモン選択とインスタンス表示")
        party_label.setObjectName("sectionLabel")

        # ポケモン選択用のドロップダウン
        # ここで選んだ ID を使ってインスタンスを生成する。
        self.pokemon_combo = QComboBox()
        self.pokemon_combo.setObjectName("selectCombo")
        self.pokemon_combo.currentIndexChanged.connect(
            self._on_pokemon_selection_changed
        )

        # 選択中のポケモンをインスタンス表示するためのボタン
        load_button = QPushButton("インスタンス表示")
        load_button.setObjectName("actionButton")
        load_button.clicked.connect(self._on_load_button_clicked)

        self.instance_info_display = QTextEdit()
        self.instance_info_display.setReadOnly(True)
        self.instance_info_display.setObjectName("infoDisplay")
        self.instance_info_display.setPlaceholderText(
            "ここに選択したポケモンのインスタンス情報が表示されます。"
        )

        left_layout.addWidget(party_label)
        left_layout.addWidget(self.pokemon_combo)
        left_layout.addWidget(load_button)
        left_layout.addItem(
            QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        damage_label = QLabel("インスタンス情報")
        damage_label.setObjectName("sectionLabel")
        right_layout.addWidget(damage_label)
        right_layout.addWidget(self.instance_info_display)

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
            QPushButton#actionButton {
                min-height: 36px;
                padding: 8px 16px;
                color: #d4d4d4;
                background-color: #0e639c;
                border: 1px solid #0e639c;
                border-radius: 6px;
            }
            QPushButton#actionButton:hover {
                background-color: #1177c1;
                border-color: #1177c1;
            }
            QPushButton#actionButton:pressed {
                background-color: #0b4f82;
                border-color: #0b4f82;
            }
            QComboBox#selectCombo {
                min-height: 36px;
                padding: 6px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                background-color: #1e1e1e;
            }
            QTextEdit#infoDisplay {
                background-color: #1b1b1b;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                color: #f0f0f0;
                font-family: 'Segoe UI', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
                font-size: 13px;
            }
            """
        )

        self._populate_pokemon_combo()
        if self.pokemon_combo.count() > 0:
            self.pokemon_combo.setCurrentIndex(0)

    def _load_pokemon_list(self) -> dict:
        """DB から `id,name` ペアを取得し、コンボボックス表示用の辞書を返す。

        返却値は GUI の選択リストに直接使える形式で、
        `pokemon_id -> pokemon_name` のマッピングとなる。
        """
        try:
            return get_selectable_pokemon_map()
        except Exception as exc:
            self._display_error(f"ポケモンリストの読み込みに失敗しました: {exc}")
            return {}

    def _populate_pokemon_combo(self) -> None:
        """選択コンボボックスに DB から読み込んだポケモンを設定する。"""
        self.pokemon_combo.clear()
        if not self.pokemon_map:
            self.pokemon_combo.addItem("ポケモンが見つかりません", -1)
            return

        for pokemon_id, pokemon_name in self.pokemon_map.items():
            self.pokemon_combo.addItem(f"{pokemon_name} ({pokemon_id})", pokemon_id)

    def _on_pokemon_selection_changed(self, index: int) -> None:
        """コンボボックスの選択変更時に発火するハンドラ。

        選択したポケモンが有効な場合、自動的に右側にインスタンス情報を表示する。
        """
        if index < 0:
            return
        pokemon_id = self.pokemon_combo.itemData(index)
        if pokemon_id is None or pokemon_id == -1:
            self.instance_info_display.clear()
            return
        self._display_pokemon_instance(int(pokemon_id))

    def _on_load_button_clicked(self) -> None:
        """「インスタンス表示」ボタンが押されたときに発火する。

        選択中のポケモン ID を取得して、インスタンス生成／表示処理を実行する。
        """
        index = self.pokemon_combo.currentIndex()
        if index < 0:
            return
        pokemon_id = self.pokemon_combo.itemData(index)
        if pokemon_id is None or pokemon_id == -1:
            self._display_error("有効なポケモンを選択してください。")
            return
        self._display_pokemon_instance(int(pokemon_id))

    def _display_pokemon_instance(self, pokemon_id: int) -> None:
        """選択したポケモン ID から `PokemonInstance` を生成し、情報を表示する。"""
        try:
            pokemon_instance = create_pokemon_by_id(pokemon_id)
            if pokemon_instance is None:
                self._display_error(
                    "選択したポケモンのインスタンスを生成できませんでした。"
                )
                return

            # インスタンスの中身を辞書化し、JSON 文字列として表示する。
            info = pokemon_instance.to_dict()
            pretty_info = json.dumps(info, ensure_ascii=False, indent=2)
            self.instance_info_display.setPlainText(pretty_info)
        except Exception as exc:
            self._display_error(f"インスタンス生成に失敗しました: {exc}")

    def _display_error(self, message: str) -> None:
        """エラー発生時に右側のテキスト領域へメッセージを表示する。"""
        self.instance_info_display.setPlainText(message)
