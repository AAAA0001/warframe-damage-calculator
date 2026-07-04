from dataclasses import dataclass

from .weapon_state import WeaponState


@dataclass
class MeleeState(WeaponState):
    """Represents stats used by melee weapons.

    Adds melee-only values for attack speed, Melee Doughty, and Melee
    Duplicate.

    ``MeleeCalculator`` fills these values from the active ``Build`` and uses
    them while calculating hit damage and damage over time.

    Used by ``Melee`` weapons.
    """
    attack_speed: float = 1.0
    melee_doughty: float = 0.0
    melee_duplicate: float = 0.0