from __future__ import annotations

from typing import ClassVar

from ..calculators import WeaponCalculator
from ..models.build import Build
from ..states.weapon import WeaponState


class WeaponFormatter[TWeaponState: WeaponState]:
    calculator_class: ClassVar[type[WeaponCalculator[TWeaponState]]] = WeaponState

    def __init__(self, base: TWeaponState) -> None:
        self.calculator: WeaponCalculator[TWeaponState] = self.calculator_class(base)

    def configure(self, build: Build) -> None:
        self.calculator.configure(build)

    def summary(self) -> str:
        raise NotImplementedError
