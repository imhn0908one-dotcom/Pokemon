import sqlite3
from typing import Optional

from .instance import PokemonInstance

DB_PATH = "pokemon_champions.db"
STAT_KEYS = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
DB_STAT_COLUMNS = [
    "hp",
    "attack",
    "defense",
    "special_attack",
    "special_defense",
    "speed",
]


def _fetch_pokemon_row(conn: sqlite3.Connection, name: str) -> Optional[dict]:
    cur = conn.cursor()
    # attempt name match then id if numeric provided
    cur.execute(
        "SELECT id, name, type_id1, type_id2, hp, attack, defense, special_attack, special_defense, speed FROM pokemon WHERE name = ? COLLATE NOCASE",
        (name,),
    )
    row = cur.fetchone()
    if row:
        keys = ["id", "name", "type_id1", "type_id2"] + STAT_KEYS
        return dict(zip(keys, row, strict=True))

    # try numeric id
    try:
        pid = int(name)
    except Exception:
        return None

    cur.execute(
        "SELECT id, name, type_id1, type_id2, hp, attack, defense, special_attack, special_defense, speed FROM pokemon WHERE id = ?",
        (pid,),
    )
    row = cur.fetchone()
    if row:
        keys = ["id", "name", "type_id1", "type_id2"] + STAT_KEYS
        return dict(zip(keys, row, strict=True))

    return None


def _fetch_learnable_moves(conn: sqlite3.Connection, pokemon_id: int) -> list:
    cur = conn.cursor()
    # This query assumes a table pokemon_move that links pokemon_id and move_id
    cur.execute(
        "SELECT DISTINCT move_id FROM pokemon_move WHERE pokemon_id = ?", (pokemon_id,)
    )
    return [row[0] for row in cur.fetchall()]


def _fetch_pokemon_row_by_id(conn: sqlite3.Connection, pid: int) -> Optional[dict]:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, type_id1, type_id2, hp, attack, defense, special_attack, special_defense, speed FROM pokemon WHERE id = ?",
        (int(pid),),
    )
    row = cur.fetchone()
    if not row:
        return None

    keys = ["id", "name", "type_id1", "type_id2"] + STAT_KEYS
    return dict(zip(keys, row, strict=True))


def create_pokemon_by_name(pokemon_name: str) -> Optional[PokemonInstance]:
    """Create a PokemonInstance from DB using pokemon_name or numeric id string.

    Returns None if the pokemon is not found.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        row = _fetch_pokemon_row(conn, pokemon_name)
        if not row:
            return None

        inst = PokemonInstance()
        inst.id = int(row["id"]) if row.get("id") is not None else 0
        inst.name = row.get("name") or ""

        types = []
        if row.get("type_id1"):
            types.append(str(row.get("type_id1")))
        if row.get("type_id2"):
            types.append(str(row.get("type_id2")))
        inst.types = types

        # base stats mapping from DB columns -> basestats
        inst.basestats = {
            "HP": int(row.get("HP", 0)),
            "Atk": int(row.get("Atk", 0)),
            "Def": int(row.get("Def", 0)),
            "SpA": int(row.get("SpA", 0)),
            "SpD": int(row.get("SpD", 0)),
            "Spe": int(row.get("Spe", 0)),
        }

        # evs default to zeros (editing added later)
        inst.evs = inst.evs  # keep default

        # genderid / natureid - default 0 unless DB provides columns
        inst.genderid = (
            int(row.get("gender_id", 0)) if row.get("gender_id") is not None else 0
        )
        inst.natureid = (
            int(row.get("nature_id", 0)) if row.get("nature_id") is not None else 0
        )

        # fetch list of learnable moves
        learnt = _fetch_learnable_moves(conn, inst.id)
        inst.learnt_move_ids = learnt

        return inst
    finally:
        conn.close()


def create_pokemon_by_id(pokemon_id: int) -> Optional[PokemonInstance]:
    """Create a PokemonInstance from DB using numeric pokemon_id (int).

    Returns None if the pokemon_id is not found.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        row = _fetch_pokemon_row_by_id(conn, int(pokemon_id))
        if not row:
            return None

        inst = PokemonInstance()
        inst.id = int(row["id"]) if row.get("id") is not None else 0
        inst.name = row.get("name") or ""

        types = []
        if row.get("type_id1"):
            types.append(str(row.get("type_id1")))
        if row.get("type_id2"):
            types.append(str(row.get("type_id2")))
        inst.types = types

        inst.basestats = {
            "HP": int(row.get("HP", 0)),
            "Atk": int(row.get("Atk", 0)),
            "Def": int(row.get("Def", 0)),
            "SpA": int(row.get("SpA", 0)),
            "SpD": int(row.get("SpD", 0)),
            "Spe": int(row.get("Spe", 0)),
        }

        inst.evs = inst.evs
        inst.genderid = (
            int(row.get("gender_id", 0)) if row.get("gender_id") is not None else 0
        )
        inst.natureid = (
            int(row.get("nature_id", 0)) if row.get("nature_id") is not None else 0
        )

        learnt = _fetch_learnable_moves(conn, inst.id)
        inst.learnt_move_ids = learnt

        return inst
    finally:
        conn.close()
