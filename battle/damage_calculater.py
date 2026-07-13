import sqlite3
import math
from contextlib import contextmanager
import stat
import types
from dataclasses import dataclass
from POKEMON.instance import PokemonInstance


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

    def damage_calculater(
        self,
        attacker: PokemonInstance,
        defender: PokemonInstance,
    ):
        pass


@dataclass
class DamageResult:
    hp_change: dict[str, list[int]]
    # how_many_times_to_kill: dict
    kill_chance: dict[str, int]
    status_change_attacker: dict[str, int]
    status_change_defender: dict[str, int]
