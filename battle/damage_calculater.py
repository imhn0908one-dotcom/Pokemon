import math
import random as rand
import sqlite3
import stat
import types
from contextlib import contextmanager
from dataclasses import dataclass

from POKEMON.instance import PokemonInstance


class Damagecalculator:
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
        
    def real_stat_calculator(
            self,
            attacker: PokemonInstance
            
    ):
        
        pass
        """
        最大HP
            種族値+能力ポイント+75
        攻撃・防御・特攻・特防・素早さ
            (種族値+能力ポイント+20)×能力補正
"""

    def damage_calculator(
        self,
        attacker: PokemonInstance,
        defender: PokemonInstance,
        move_id: int
    ):
        move_data = self.move_basic_data(move_id)
        # ダメージ = (((レベル×2/5+2)×威力×A/D)/50+2)×範囲補正×おやこあい補正×天気補正×急所補正×乱数補正×タイプ一致補正×相性補正×やけど補正×M

        # 持ち物取得
        # 持ち物、による威力補正　 これの実装により”””damage = math.floor(22*move_data["power"])”””の変更が必要
        
        damage = math.floor(22 * move_data["power"])
        damage = math.floor(damage * attacker.basestats["Atk"])
        damage = math.floor(damage / defender.basestats["Def"])

        return damage


@dataclass
class DamageResult:
    hp_change: dict[str, list[int]]
    # how_many_times_to_kill: dict
    kill_chance: dict[str, int]
    status_change_attacker: dict[str, int]
    status_change_defender: dict[str, int]