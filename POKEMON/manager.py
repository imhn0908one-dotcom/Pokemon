import sqlite3
from typing import Dict

from .factory import DB_PATH


def get_selectable_pokemon_map() -> Dict[int, str]:
    """Return a mapping of Pokemon IDs to Pokemon names for selection lists.

    This function reads the `pokemon` table from the database and produces a dict
    where each key is the Pokemon ID and each value is the Pokemon name.

    The returned dict is suitable for GUI dropdowns, selection menus, or any
    selection logic where the caller needs to show the name and keep the ID as
    the stable identifier.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM pokemon ORDER BY id")
        rows = cursor.fetchall()

        selection_map: Dict[int, str] = {}
        for row in rows:
            pokemon_id, pokemon_name = row
            if pokemon_id is None or pokemon_name is None:
                continue
            selection_map[int(pokemon_id)] = str(pokemon_name)

        return selection_map
    finally:
        conn.close()


print(get_selectable_pokemon_map())
