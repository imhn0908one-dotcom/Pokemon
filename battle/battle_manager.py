import sqlite3

import toml


class Single_Battle_Manager:
    def __init__(
        self,
        A_pokemon,
        B_pokemon,
    ):
        self.A_pokemon = A_pokemon
        self.B_pokemon = B_pokemon
        self.db_path = A_pokemon.db_path
        self.turncount = 0
        self.winner = None

    def move_basic_data(self, move_id) -> dict:

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
            return None

    def move_meta_data(self, move_id) -> dict:
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
                return None
        except sqlite3.OperationalError:
            return None
        if row:
            return dict(row)
        else:
            return None

    def calculate_final_priority(self, pokeinstance, move_id) -> int:
        final_priority = self.move_basic_data(move_id)["priority"]
        # other method to calculate final priority(under development)
        print(f"final priority: {final_priority}")

        return final_priority


def toml_input(toml_path) -> dict:
    with open(toml_path, "r", encoding="utf-8") as f:
        data = toml.load(f)
    return data
