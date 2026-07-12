from typing import TypedDict

from ..utils import DamageType


class WeaponFields(TypedDict, total=False):
    name: str | None
    type: str | None
    damage: dict[DamageType, float]
    forced_procs: dict[DamageType, float]
    crit_chance: float
    crit_damage: float
    status_chance: float
