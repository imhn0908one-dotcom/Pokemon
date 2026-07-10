from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PokemonInstance:
    id: int = 0
    name: str = ""
    types: List[str] = field(default_factory=list)
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
    genderid: int = 0
    natureid: int = 0
    learnt_move_ids: List[int] = field(default_factory=list)
    selected_move_ids: List[int] = field(default_factory=lambda: [0, 0, 0, 0])

    def to_dict(self) -> Dict:
        return {
            "id": int(self.id),
            "name": str(self.name),
            "types": list(self.types),
            "basestats": dict(self.basestats),
            "evs": dict(self.evs),
            "genderid": int(self.genderid),
            "natureid": int(self.natureid),
            "learnt_move_ids": list(self.learnt_move_ids),
            "selected_move_ids": list(self.selected_move_ids),
        }
