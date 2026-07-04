from dataclasses import dataclass

from .weapon import WeaponState


@dataclass
class MeleeState(WeaponState):
    attack_speed: float = 1.0
    melee_doughty: float = 0.0
    melee_duplicate: float = 0.0