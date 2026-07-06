import sqlite3
import math
import toml


class Pokemon_Instance:
    def __init__(self, pokemon_dict, db_path="pokemon_champions.db"):

        # from pokemon_dict
        self.db_path = db_path
        self.id = pokemon_dict["id"]
        self.name = pokemon_dict["name"]
        self.moves = pokemon_dict.get("moves", [])
        self.level = pokemon_dict.get("level", 50)
        self.nature = pokemon_dict.get("nature", pokemon_dict.get("nature_id"))
        raw_evs = pokemon_dict.get("evs", {}) or {}
        self.evs = {
            "hp": raw_evs.get("hp", 0),
            "attack": raw_evs.get("attack", 0),
            "defense": raw_evs.get("defense", 0),
            "sp_attack": raw_evs.get("sp_attack", 0),
            "sp_defense": raw_evs.get("sp_defense", 0),
            "speed": raw_evs.get("speed", 0),
        }
        self.ability = pokemon_dict.get("ability", pokemon_dict.get("ability_id", 0))
        # 初期化
        self.condition = "NONE"
        self.moves_pp = {}
        self.ranks = {
            "attack": 0,
            "defense": 0,
            "sp_attack": 0,
            "sp_defense": 0,
            "speed": 0,
            "accuracy": 0,
            "evasion": 0,
        }

        # --- 種族値 ---
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT hp,attack,defense,special_attack,special_defense,speed FROM pokemon WHERE id = ?",
            (self.id,),
        )
        (
            base_hp,
            base_attack,
            base_defense,
            base_sp_attack,
            base_sp_defense,
            base_speed,
        ) = cursor.fetchone()
        cursor.execute(
            "select name from ability_basicdata where id = ?", (self.ability,)
        )
        ability_row = cursor.fetchone()
        self.ability_name = (
            ability_row[0] if ability_row and ability_row[0] else "（未選択）"
        )
        # 実数値の計算
        self.hp_max = (
            (base_hp * 2 + 31) * self.level // 100 + self.level + 10 + self.evs["hp"]
        )
        calc_attack = (
            (base_attack * 2 + 31) * self.level // 100 + 5 + self.evs["attack"]
        )
        calc_defense = (
            (base_defense * 2 + 31) * self.level // 100 + 5 + self.evs["defense"]
        )
        calc_sp_attack = (
            (base_sp_attack * 2 + 31) * self.level // 100 + 5 + self.evs["sp_attack"]
        )
        calc_sp_defense = (
            (base_sp_defense * 2 + 31) * self.level // 100 + 5 + self.evs["sp_defense"]
        )
        calc_speed = (base_speed * 2 + 31) * self.level // 100 + 5 + self.evs["speed"]
        self.hp = self.hp_max
        self.pokemon_accuracy = 100
        self.evasion = 100

        # --- nature 補正 ---
        # 1. 計算した基本実数値を、対応するIDの辞書にまとめておく

        stats = {
            2: calc_attack,
            3: calc_defense,
            4: calc_sp_attack,
            5: calc_sp_defense,
            6: calc_speed,
        }

        # 2. 性格補正データを取得
        nature_row = cursor.execute(
            "SELECT increased_stat_id, decreased_stat_id, name FROM nature_data WHERE id = ?",
            (self.nature,),
        ).fetchone()
        self.nature_name = nature_row[2]
        if nature_row:
            inc_id, dec_id, _ = nature_row

            # 上昇・下降のIDがあれば、そのキーの値を1.1倍 / 0.9倍に書き換える
            if inc_id in stats:
                stats[inc_id] = int(stats[inc_id] * 1.1)
            if dec_id in stats:
                stats[dec_id] = int(stats[dec_id] * 0.9)

        # 3. 最終的な数値をクラスの変数にガツンと代入して完成！
        self.attack = stats[2]
        self.defense = stats[3]
        self.sp_attack = stats[4]
        self.sp_defense = stats[5]
        self.speed = stats[6]

        self.init_moves_and_pp(self.db_path)

        cursor.close()
        conn.close()

    @classmethod
    def from_toml(cls, toml_path, pokemon_index, db_path="pokemon_champions.db"):
        with open(toml_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        party = data.get("pokemon")
        if party is None or not isinstance(party, list):
            raise ValueError("TOML file does not contain a valid pokemon list")
        if not isinstance(pokemon_index, int):
            raise ValueError("pokemon_index must be an integer")
        if pokemon_index < 0 or pokemon_index >= len(party):
            raise IndexError("pokemon_index is out of range")

        pokemon_entry = party[pokemon_index]
        pokemon_dict = {
            "id": pokemon_entry.get("pokemon_id", pokemon_entry.get("id")),
            "name": pokemon_entry.get("name"),
            "moves": pokemon_entry.get("moves", []),
            "level": pokemon_entry.get("level", 50),
            "nature": pokemon_entry.get("nature_id", pokemon_entry.get("nature")),
            "evs": pokemon_entry.get("evs", {}),
            "ability": pokemon_entry.get("ability_id", pokemon_entry.get("ability")),
        }

        if pokemon_dict["id"] is None:
            raise ValueError("Pokemon entry must include pokemon_id or id")

        return cls(pokemon_dict, db_path=db_path)

    def init_moves_and_pp(self, db_path):
        """
        渡された技IDリストから、技の『最大PP』と『技名』を同時に取得し、
        それぞれの辞書に保存する。
        """
        if not self.moves:
            return

        # 技名管理用の辞書を初期化
        self.moves_name = {}

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for move_id in self.moves:
            if move_id == 0:
                continue

            try:
                # 💡 pp と一緒に name（技名）も同時に SELECT してくる！
                cursor.execute(
                    "SELECT pp, name FROM move_basicdata WHERE id = ?", (move_id,)
                )
                row = cursor.fetchone()

                if row:
                    base_pp, move_name = row[0], row[1]
                else:
                    base_pp, move_name = 20, f"わざ(ID:{move_id})"

            except sqlite3.Error:
                base_pp, move_name = 20, f"わざ(ID:{move_id})"

            # 1. チャンピオンズルール適用済みの最大PPを計算して格納
            if base_pp == 5:
                max_pp = 8
            elif base_pp == 10:
                max_pp = 16
            elif base_pp == 15:
                max_pp = 24
            elif base_pp >= 20:
                max_pp = 20
            else:
                max_pp = base_pp

            self.moves_pp[move_id] = max_pp

            # 2. 💡 技ID と 技名 を辞書にがっつり紐付ける！
            self.moves_name[move_id] = move_name

        conn.close()

    def get_rank_multiplier(self, rank):
        if rank >= 0:
            return (2 + rank) / 2
        else:
            return (2 - rank) / 2

    def get_effective_stat(self, stat):
        # 基本値を取得
        base_value = getattr(self, stat)
        # 倍率を計算
        multiplier = self.get_rank_multiplier(self.ranks[stat])
        # 倍率に基本値をかける
        return math.floor(base_value * multiplier)

    def show_status(self):
        """
        現在のポケモンの全ステータス（実数値、能力ポイント、現在のランク、HP、PP）
        をコンソールに美しく一発表示するデバッグ・確認用関数。
        """
        print("=" * 45)
        print(" ［ ポケモンステータス確認 ］")
        print(f" 名前: {self.name} (ID: {self.id})")
        print(f" 状態異常: [{self.condition}]")
        print(f" HP  : {self.hp} / {self.hp_max}")
        print("-" * 45)
        print(f" 性格：{self.nature}, 名前：{self.nature_name}")
        print(f" 特性：{self.ability}, 名前：{self.ability_name}")
        print("-" * 45)

        # 各ステータスの名前マッピング
        stats_to_show = [
            ("attack", "攻撃力"),
            ("defense", "防御力"),
            ("sp_attack", "特攻力"),
            ("sp_defense", "特防力"),
            ("speed", "素早さ"),
        ]

        for eng_name, jpn_name in stats_to_show:
            print(f" {jpn_name}: {self.get_effective_stat(eng_name)}")

        print("-" * 45)
        print(" 覚えている技と現在のPP (チャンピオンズルール適用済):")
        for move_id, current_pp in self.moves_pp.items():
            print(
                f"  ・技ID: {move_id:<3} , 名前: {self.moves_name[move_id]} [ PP: {current_pp} ]"
            )
        print("=" * 45)

    def toml_input(toml_path) -> dict:
        with open(toml_path, "r", encoding="utf-8") as f:
            data = toml.load(f)
        return data
