import sqlite3
import math
from contextlib import contextmanager


class DamageCalculater:
    """ダメージ計算ロジックをまとめるための雛形クラス。"""

    def __init__(self):
        self.db_path = "pokemon_champions.db"

    @contextmanager
    def _database(self):
        """DB接続をコンテキストマネージャとして扱う。"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn.cursor()
        finally:
            conn.close()

    def move_basic_data(self, move_id) -> dict:
        """指定技IDの基本データを取得する。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM move_basicdata WHERE id = ?",
            (move_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        else:
            return None  # type: ignore

    def move_meta_data(self, move_id) -> dict:
        """指定技IDのメタデータを取得する。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM move_meta WHERE id = ?", (move_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return dict(row)
            else:
                return None  # type: ignore
        except sqlite3.OperationalError:
            return None  # type: ignore
        if row:
            return dict(row)
        else:
            return None

    def calculate_damage(self, attacker, defender, move_index):
        """ダメージ計算の雛形。今後の実装に向けたプレースホルダー。"""
        movedata = self.move_basic_data(attacker.moves[move_index])
        damage = math.floor(2 * attacker.level / 5) + 2
        damage_class = movedata["damage_class_id"]  # タイプによって計算などが変化。
        # 1 = 変化, 2 = 物理, 3 = 特殊

        


        if damage_class == 1:
            pass
        return damage
