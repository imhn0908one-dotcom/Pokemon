from dataclasses import dataclass
from POKEMON.instance import PokemonInstance
from FIELD.state import BattleField, SideField
from PySide6.QtCore import QObject


# BATTLE/battle_manager.py
# receive from GUI and send calculator
class BattleManager(QObject):
    def __init__(self) -> None:
        self.attacker: PokemonInstance | None = None
        self.defender: PokemonInstance | None = None
        self.field: BattleField = BattleField()
        self.attacker_side: SideField = SideField()
        self.defender_side: SideField = SideField()

    def set_attacker(self, attacker: PokemonInstance) -> None:
        self.attacker = attacker

    def set_defender(self, defender: PokemonInstance) -> None:
        self.defender = defender

    def can_calculate(self) -> bool:
        """Check if both attacker and defender are set for calculation."""
        return self.attacker is not None and self.defender is not None

    def reset(self) -> None:
        self.attacker = None
        self.defender = None
