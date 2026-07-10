import sqlite3
import toml
from typing import Optional, List, Dict


class PartyBuilderLogic:
    def __init__(self, db_path="pokemon_champions.db"):
        self.db_path = db_path

    def _get_cursor(self):
        """必要なときにだけDB接続を作るか、コンテキストマネージャで使うためのヘルパー"""
        conn = sqlite3.connect(self.db_path)
        return conn, conn.cursor()

    # --- 1. ポケモン検証 & データ取得 ---
    def get_pokemon_data(self, pokemon_id) -> Optional[dict]:
        """ポケモンIDが有効なら名前を返す。無効なら None"""
        conn, cursor = self._get_cursor()
        cursor.execute("SELECT name FROM pokemon WHERE id = ?", (pokemon_id,))
        row = cursor.fetchone()
        conn.close()
        return {"pokemon_id": pokemon_id, "name": row[0]} if row else None

    # --- 2. 技の検証 & 候補取得 ---
    def get_learnable_moves(self, pokemon_id) -> List[int]:
        """そのポケモンが覚えられる技IDのリストを返す"""
        conn, cursor = self._get_cursor()
        cursor.execute(
            "SELECT move_id FROM pokemon_move WHERE pokemon_id = ?",
            (pokemon_id,),
        )
        move_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return move_ids

    def validate_moves(self, pokemon_id, selected_move_ids) -> bool:
        """選ばれた4つの技に重複がなく、かつ本当に覚えられるか検証する.IDSはintのリスト"""
        if len(selected_move_ids) != len(set(selected_move_ids)):
            return False  # 重複あり

        learnable = self.get_learnable_moves(pokemon_id)
        return all(m_id in learnable for m_id in selected_move_ids)

    # --- 3. 性格データの取得 ---
    def get_nature_list(self) -> List[Dict]:
        """CUIの選択肢に表示するための性格IDと名前のリストを返す"""
        conn, cursor = self._get_cursor()
        cursor.execute("SELECT id, name FROM nature_data ORDER BY id")
        natures = [
            {"nature_id": row[0], "nature_name": row[1]} for row in cursor.fetchall()
        ]
        conn.close()
        return natures

    def get_nature_name(self, nature_id) -> Optional[str]:
        """性格IDから性格名を取得する（存在しなければNone）"""
        conn, cursor = self._get_cursor()
        cursor.execute("SELECT name FROM nature_data WHERE id = ?", (nature_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    # --- 4. 特性データの取得 ---
    def get_available_abilities(self, pokemon_id) -> List[Dict]:
        """そのポケモンが持つ特性IDと名前の辞書リストを返す"""
        conn, cursor = self._get_cursor()
        cursor.execute(
            "SELECT ability_id FROM pokemon_ability WHERE pokemon_id = ?",
            (pokemon_id,),
        )
        ability_ids = [row[0] for row in cursor.fetchall()]
        if not ability_ids:
            conn.close()
            return []

        placeholders = ", ".join("?" for _ in ability_ids)
        query = f"SELECT id, name FROM ability_basicdata WHERE id IN ({placeholders})"
        cursor.execute(query, ability_ids)
        abilities = [
            {"ability_id": row[0], "ability_name": row[1]} for row in cursor.fetchall()
        ]
        conn.close()
        return abilities

    # --- 5. 努力値（ポイント）のバリデーション ---
    def validate_evs(self, evs) -> bool:
        """各ステータスが0-32に収まっており、合計が66以下かチェック"""
        stat_names = [
            "hp",
            "attack",
            "defense",
            "sp_attack",
            "sp_defense",
            "speed",
        ]
        # 必要なキーが揃っているか
        if not all(stat in evs for stat in stat_names):
            return False
        # 各値が 0 〜 32 か
        if not all(0 <= evs[stat] <= 32 for stat in stat_names):
            return False
        # 合計が 66 以下か
        return sum(evs.values()) <= 66

    # --- 6. 最終データの書き出し ---
    def save_party(self, party_name, pokemon_entries):
        """受け取った綺麗なデータセットをTOMLに保存する"""
        filename = f"{party_name}.toml"
        party_data = {"party_name": party_name, "pokemon": pokemon_entries}
        with open(filename, "w", encoding="utf-8") as f:
            toml.dump(party_data, f)
        return filename
