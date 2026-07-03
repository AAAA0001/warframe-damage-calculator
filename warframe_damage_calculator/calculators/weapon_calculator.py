from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.states import WeaponState
    from ..models.weapon import Weapon

class WeaponCalculator:
    def __init__(self, weapon: Weapon[WeaponState]) -> None:
        self.weapon: Weapon[WeaponState] = weapon

    @cached_property
    def average_crit_chance(self) -> float:
        return self.weapon.effective.crit_chance

    @cached_property
    def average_crit_multiplier(self) -> float:
        return 1 + self.average_crit_chance * (self.weapon.effective.crit_damage - 1)

    @cached_property
    def total_dph(self) -> float:
        return self.flat_dph + self.flat_dotph

    @cached_property
    def total_dps(self) -> float:
        return self.flat_dps + self.flat_dotps
    
    def clear_cache(self) -> None:
        for cls in type(self).mro():
            for name, attr in cls.__dict__.items():
                if isinstance(attr, cached_property):
                    self.__dict__.pop(name, None)
