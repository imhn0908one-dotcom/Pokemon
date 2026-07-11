import sqlite3
import os
import sys
from typing import Dict, Iterable, List

try:
    from POKEMON.factory import DB_PATH
except ImportError:
    try:
        from .factory import DB_PATH
    except ImportError:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        from POKEMON.factory import DB_PATH


def _fetch_move_name_map(
    conn: sqlite3.Connection, move_ids: Iterable[int]
) -> Dict[int, str]:
    if not move_ids:
        return {}

    placeholders = ",".join("?" for _ in move_ids)
    query = f"SELECT id, name FROM move_basicdata WHERE id IN ({placeholders})"
    cursor = conn.cursor()
    cursor.execute(query, tuple(move_ids))
    return {int(row[0]): str(row[1]) for row in cursor.fetchall() if row[0] is not None}


def learnt_move_names_to_dict(
    learnt_move_ids: List[int], separator: str = " / "
) -> Dict[str, object]:
    """Convert a learnt move ID list into a dict containing joined move names."""
    normalized_ids = [
        int(move_id) for move_id in learnt_move_ids if move_id is not None
    ]
    if not normalized_ids:
        return {
            "learnt_move_ids": [],
            "learnt_move_name_list": [],
            "learnt_move_names": "",
        }

    conn = sqlite3.connect(DB_PATH)
    try:
        name_map = _fetch_move_name_map(conn, normalized_ids)
    finally:
        conn.close()

    name_list = [
        name_map.get(move_id, f"Unknown({move_id})") for move_id in normalized_ids
    ]
    joined_names = separator.join(name_list)

    return {
        "learnt_move_ids": normalized_ids,
        "learnt_move_name_list": name_list,
        "learnt_move_names": joined_names,
    }


def get_nature_name_map() -> Dict[int, str]:
    """Return a mapping of nature IDs to nature names."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM nature_data ORDER BY id")
        rows = cursor.fetchall()

        nature_map: Dict[int, str] = {}
        for row in rows:
            nature_id, nature_name = row
            if nature_id is None or nature_name is None:
                continue
            nature_map[int(nature_id)] = str(nature_name)

        return nature_map
    finally:
        conn.close()


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
