import threading
from dataclasses import dataclass, field
from typing import Dict, List

from pokebase import item


@dataclass
class PokemonInstance:
    id: int = 0  # pokemon ID
    name: str = ""  # pokemon name
    types: List[str] = field(default_factory=list)  # length 1~4
    basestats: Dict[str, int] = field(
        default_factory=lambda: {
            "HP": 0,
            "Atk": 0,
            "Def": 0,
            "SpA": 0,
            "SpD": 0,
            "Spe": 0,
        }
    )
    evs: Dict[str, int] = field(
        default_factory=lambda: {
            "HP": 0,
            "Atk": 0,
            "Def": 0,
            "SpA": 0,
            "SpD": 0,
            "Spe": 0,
        }
    )
    rank: Dict[str, int] = field(
        default_factory=lambda: {
            "Atk": 0,
            "Def": 0,
            "SpA": 0,
            "SpD": 0,
            "Spe": 0,
            "Acuracy_rate": 0,
            "Evasion_rate": 0,
        }
    )
    gender_Id: int = 0
    nature_Id: int = 0
    stat_change: Dict[str, int] = field(default_factory=dict)
    """""status change by nature"""""
    item_Id: int = 0

    # moves
    learnt_move_ids: List[int] = field(default_factory=list)
    selected_move_ids: List[int] = field(default_factory=lambda: [0, 0, 0, 0])

    # internal lock to make updates atomic when GUI modifies fields concurrently
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def update_ev(self, key: str, value: int) -> None:
        """Update a single EV value with validation.

        - `key`: one of the stat keys in `evs` (e.g. 'HP','Atk',...)
        - `value`: new EV value (int)

        Rules enforced:
        - per-stat: 0 <= value <= 32
        - total EVs after change <= 66

        Raises ValueError on validation failure.
        """
        with self._lock:
            if key not in self.evs:
                raise ValueError(f"Unknown EV stat: {key}")

            if not isinstance(value, int) or value < 0 or value > 32:
                raise ValueError("EV value must be integer between 0 and 32")

            current = int(self.evs.get(key, 0))
            total = sum(int(v) for v in self.evs.values()) - current + value
            if total > 66:
                raise ValueError(f"Total EVs would exceed 66 (would be {total})")

            self.evs[key] = int(value)

    def is_move_learned(self, move_id: int) -> bool:
        """Return True if `move_id` is present in `learnt_move_ids`."""
        return int(move_id) in list(self.learnt_move_ids)

    def set_selected_move(self, index: int, move_id: int) -> None:
        """Set selected move at `index` (0-3) after validation.

        - `index`: slot index 0..3
        - `move_id`: move id (int). Use 0 to clear the slot.

        Raises IndexError or ValueError on invalid input.
        """
        with self._lock:
            if not (0 <= index <= 3):
                raise IndexError("Move slot index must be between 0 and 3")

            if move_id != 0 and not self.is_move_learned(int(move_id)):
                raise ValueError(f"Move id {move_id} is not learnable by this Pokemon")

            self.selected_move_ids[index] = int(move_id)

    def to_dict(self) -> Dict:
        return {
            "id": int(self.id),
            "name": str(self.name),
            "types": list(self.types),
            "basestats": dict(self.basestats),
            "evs": dict(self.evs),
            "genderid": int(self.gender_Id),
            "natureid": int(self.nature_Id),
            "itemid": int(self.item_Id),
            "learnt_move_ids": list(self.learnt_move_ids),
            "selected_move_ids": list(self.selected_move_ids),
        }
