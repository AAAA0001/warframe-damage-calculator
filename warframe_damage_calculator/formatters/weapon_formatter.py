from __future__ import annotations

from ..calculators import WeaponCalculator
from ..states import WeaponState


class WeaponFormatter[TWeaponState: WeaponState]:
    """Base formatter for weapon stats.

    A formatter reads values from a calculator and turns them into a readable
    text summary.

    Stores the calculator and defines the ``summary`` method. It does not
    calculate damage, apply builds, or change weapon stats.

    Specialized formatters provide the actual summary text for each weapon
    family.
    """
    def __init__(self, calculator: WeaponCalculator[TWeaponState]) -> None:
        self.calculator: WeaponCalculator[TWeaponState] = calculator

    def summary(self) -> str:
        raise NotImplementedError
