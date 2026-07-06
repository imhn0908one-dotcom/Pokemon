import os
from contextlib import contextmanager
import sqlite3
import toml


class PartyManagerLogic:
    """パーティデータの作成・読み込み・保存・更新を担当するロジック層。"""

    DEFAULT_PARTY_SIZE = 6
    DEFAULT_LEVEL = 50
    DEFAULT_EMPTY_NAME = "（未選択）"
    DEFAULT_EMPTY_ABILITY_NAME = "（未選択）"
    DEFAULT_EMPTY_MOVE = 0
    DEFAULT_PARTY_DIR = "party"
    STAT_NAMES = (
        "hp",
        "attack",
        "defense",
        "special_attack",
        "special_defense",
        "speed",
    )
    MAX_EV_PER_STAT = 32
    MAX_EV_TOTAL = 66

    def __init__(self, db_path="pokemon_champions.db"):
        self.db_path = db_path
        self.party_path = None
        self.party_data = None

    def _ensure_party_dir(self):
        """partyディレクトリが存在しなければ作成する。"""
        if not os.path.exists(self.DEFAULT_PARTY_DIR):
            os.makedirs(self.DEFAULT_PARTY_DIR, exist_ok=True)

    def _resolve_party_path(self, filepath):
        """相対パスをpartyディレクトリ配下に解決する。"""
        if filepath is None:
            return None
        if os.path.isabs(filepath):
            return filepath
        if os.path.dirname(filepath):
            return filepath
        return os.path.join(self.DEFAULT_PARTY_DIR, filepath)

    @contextmanager
    def _database(self):
        """DB接続をコンテキストマネージャとして扱うためのヘルパー。"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn.cursor()
        finally:
            conn.close()

    def _fetch_one(self, sql, params=()):
        with self._database() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def get_pokemon_name(self, pokemon_id):
        if pokemon_id == 0:
            return self.DEFAULT_EMPTY_NAME
        row = self._fetch_one("SELECT name FROM pokemon WHERE id = ?", (pokemon_id,))
        return row[0] if row else None

    def get_nature_name(self, nature_id):
        row = self._fetch_one("SELECT name FROM nature_data WHERE id = ?", (nature_id,))
        return row[0] if row else None

    def get_nature_list(self):
        with self._database() as cursor:
            cursor.execute("SELECT id, name FROM nature_data ORDER BY id")
            return [
                {"nature_id": row[0], "nature_name": row[1]}
                for row in cursor.fetchall()
            ]

    def get_default_nature(self):
        row = self._fetch_one("SELECT id, name FROM nature_data ORDER BY id LIMIT 1")
        if row:
            return row[0], row[1]
        return 1, "Hardy"

    def get_ability_name(self, ability_id):
        if ability_id == 0:
            return self.DEFAULT_EMPTY_ABILITY_NAME
        row = self._fetch_one(
            "SELECT name FROM ability_basicdata WHERE id = ?", (ability_id,)
        )
        return row[0] if row else None

    def get_learnable_moves(self, pokemon_id):
        if pokemon_id == 0:
            return []
        with self._database() as cursor:
            cursor.execute(
                "SELECT move_id FROM pokemon_move WHERE pokemon_id = ?",
                (pokemon_id,),
            )
            return [row[0] for row in cursor.fetchall()]

    def get_available_abilities(self, pokemon_id):
        if pokemon_id == 0:
            return []
        with self._database() as cursor:
            cursor.execute(
                "SELECT ability_id FROM pokemon_ability WHERE pokemon_id = ?",
                (pokemon_id,),
            )
            ability_ids = [row[0] for row in cursor.fetchall()]
            if not ability_ids:
                return []
            placeholders = ", ".join("?" for _ in ability_ids)
            query = (
                f"SELECT id, name FROM ability_basicdata WHERE id IN ({placeholders})"
            )
            cursor.execute(query, ability_ids)
            return [
                {"ability_id": row[0], "ability_name": row[1]}
                for row in cursor.fetchall()
            ]

    def create_empty_party(self, party_name, filepath=None):
        """空のパーティを作成し、TOMLとして保存する。"""
        if not party_name or not isinstance(party_name, str):
            raise ValueError("party_name must be a non-empty string")

        self._ensure_party_dir()
        self.party_path = self._resolve_party_path(filepath or f"{party_name}.toml")
        default_nature_id, default_nature_name = self.get_default_nature()
        self.party_data = {
            "party_name": party_name,
            "pokemon": [
                self._build_empty_slot(default_nature_id, default_nature_name)
                for _ in range(self.DEFAULT_PARTY_SIZE)
            ],
        }
        self.save_changes()
        return self.party_path

    def load_party(self, filepath):
        """既存のTOMLパーティを読み込んでメモリ上に展開する。"""
        if not filepath:
            raise ValueError("filepath must be provided")
        resolved_path = self._resolve_party_path(filepath)
        if not os.path.exists(resolved_path):  # type: ignore
            raise FileNotFoundError(f"Party file not found: {resolved_path}")
        with open(resolved_path, "r", encoding="utf-8") as handle:  # type: ignore
            self.party_data = toml.load(handle)
        self.party_path = resolved_path
        return self.party_data

    def save_changes(self, filepath=None):
        """現在のパーティ内容をTOMLに保存する。"""
        if self.party_data is None:
            raise RuntimeError("No party is loaded to save.")
        if filepath:
            self._ensure_party_dir()
            self.party_path = self._resolve_party_path(filepath)
        if not self.party_path:
            raise RuntimeError("No file path available for saving.")
        self._ensure_party_dir()
        with open(self.party_path, "w", encoding="utf-8") as handle:
            toml.dump(self.party_data, handle)
        return self.party_path

    def _build_empty_slot(self, default_nature_id, default_nature_name):
        """空のパーティスロットの初期構造を返す。"""
        return {
            "pokemon_id": 0,
            "name": self.DEFAULT_EMPTY_NAME,
            "level": self.DEFAULT_LEVEL,
            "nature_id": default_nature_id,
            "nature_name": default_nature_name,
            "ability_id": 0,
            "ability_name": self.DEFAULT_EMPTY_ABILITY_NAME,
            "moves": [self.DEFAULT_EMPTY_MOVE] * 4,
            "evs": {stat: 0 for stat in self.STAT_NAMES},
        }

    def _validate_index(self, index):
        if not isinstance(index, int):
            raise ValueError("index must be an integer")
        if index < 0 or index >= self.DEFAULT_PARTY_SIZE:
            raise IndexError("index must be between 0 and 5")

    def _validate_stat_name(self, stat_name):
        if stat_name not in self.STAT_NAMES:
            raise ValueError(f"Invalid stat name: {stat_name}")

    def change_pokemon_species(self, index, pokemon_id):
        self._validate_index(index)
        if self.party_data is None:
            raise RuntimeError("No party is loaded.")

        if pokemon_id == 0:
            default_nature_id, default_nature_name = self.get_default_nature()
            self.party_data["pokemon"][index] = self._build_empty_slot(
                default_nature_id, default_nature_name
            )
            return self.save_changes()

        pokemon_name = self.get_pokemon_name(pokemon_id)
        if pokemon_name is None:
            raise ValueError(f"Unknown pokemon_id: {pokemon_id}")

        existing_nature_id = self.party_data["pokemon"][index].get("nature_id")
        nature_id = (
            existing_nature_id
            if self.get_nature_name(existing_nature_id)
            else self.get_default_nature()[0]
        )
        nature_name = self.get_nature_name(nature_id) or self.get_default_nature()[1]

        self.party_data["pokemon"][index].update({
            "pokemon_id": pokemon_id,
            "name": pokemon_name,
            "level": self.DEFAULT_LEVEL,
            "ability_id": 0,
            "ability_name": self.DEFAULT_EMPTY_ABILITY_NAME,
            "moves": [self.DEFAULT_EMPTY_MOVE] * 4,
            "evs": {stat: 0 for stat in self.STAT_NAMES},
            "nature_id": nature_id,
            "nature_name": nature_name,
        })
        return self.save_changes()

    def change_pokemon_ev(self, index, stat_name, value):
        self._validate_index(index)
        if self.party_data is None:
            raise RuntimeError("No party is loaded.")
        self._validate_stat_name(stat_name)
        if not isinstance(value, int) or value < 0 or value > self.MAX_EV_PER_STAT:
            raise ValueError(
                f"EV must be an integer between 0 and {self.MAX_EV_PER_STAT}"
            )

        current_total = (
            sum(self.party_data["pokemon"][index]["evs"].values())
            - self.party_data["pokemon"][index]["evs"][stat_name]
            + value
        )
        if current_total > self.MAX_EV_TOTAL:
            raise ValueError(f"EV total cannot exceed {self.MAX_EV_TOTAL}")

        self.party_data["pokemon"][index]["evs"][stat_name] = value
        return self.save_changes()

    def change_pokemon_move(self, index, slot_index, move_id):
        self._validate_index(index)
        if self.party_data is None:
            raise RuntimeError("No party is loaded.")
        if not isinstance(slot_index, int) or slot_index < 0 or slot_index > 3:
            raise IndexError("slot_index must be between 0 and 3")
        if not isinstance(move_id, int) or move_id < 0:
            raise ValueError("move_id must be a non-negative integer")

        pokemon_id = self.party_data["pokemon"][index]["pokemon_id"]
        if pokemon_id == 0 and move_id != 0:
            raise ValueError("Cannot assign a move to an empty slot.")

        if move_id != 0:
            learnable = self.get_learnable_moves(pokemon_id)
            if move_id not in learnable:
                raise ValueError("This move is not learnable by the selected Pokemon.")

        self.party_data["pokemon"][index]["moves"][slot_index] = move_id
        return self.save_changes()

    def change_pokemon_moves(self, index, move_ids):
        self._validate_index(index)
        if self.party_data is None:
            raise RuntimeError("No party is loaded.")
        if not isinstance(move_ids, list) or len(move_ids) != 4:
            raise ValueError("move_ids must be a list of four integers")
        if len(move_ids) != len(set(move_ids)):
            raise ValueError("Duplicate move IDs are not allowed.")
        if not all(isinstance(move_id, int) and move_id >= 0 for move_id in move_ids):
            raise ValueError("All move IDs must be non-negative integers")

        pokemon_id = self.party_data["pokemon"][index]["pokemon_id"]
        if pokemon_id == 0 and any(move_id != 0 for move_id in move_ids):
            raise ValueError("Cannot assign moves to an empty slot.")

        learnable = self.get_learnable_moves(pokemon_id)
        for move_id in move_ids:
            if move_id != 0 and move_id not in learnable:
                raise ValueError(
                    "One or more moves are not learnable by the selected Pokemon."
                )

        self.party_data["pokemon"][index]["moves"] = move_ids
        return self.save_changes()

    def change_pokemon_nature(self, index, nature_id):
        self._validate_index(index)
        if self.party_data is None:
            raise RuntimeError("No party is loaded.")
        nature_name = self.get_nature_name(nature_id)
        if nature_name is None:
            raise ValueError(f"Unknown nature_id: {nature_id}")

        self.party_data["pokemon"][index]["nature_id"] = nature_id
        self.party_data["pokemon"][index]["nature_name"] = nature_name
        return self.save_changes()

    def change_pokemon_ability(self, index, ability_id):
        self._validate_index(index)
        if self.party_data is None:
            raise RuntimeError("No party is loaded.")

        pokemon_id = self.party_data["pokemon"][index]["pokemon_id"]
        if pokemon_id == 0 and ability_id != 0:
            raise ValueError("Cannot assign an ability to an empty slot.")

        if ability_id != 0:
            abilities = self.get_available_abilities(pokemon_id)
            if ability_id not in [entry["ability_id"] for entry in abilities]:
                raise ValueError(
                    "This ability is not available for the selected Pokemon."
                )

        ability_name = self.get_ability_name(ability_id)
        self.party_data["pokemon"][index]["ability_id"] = ability_id
        self.party_data["pokemon"][index]["ability_name"] = ability_name
        return self.save_changes()

    def get_current_party(self):
        """現在のパーティデータを取得する。"""
        return self.party_data
