from __future__ import annotations

from ..calculators import WeaponCalculator
from ..formatters import WeaponFormatter
from ..states.weapon_state import WeaponState
from .build import Build


class Weapon:
    calculator_class = WeaponCalculator
    formatter_class = WeaponFormatter

    def __init__(self, base: WeaponState):
        self.stats = self.calculator_class(base)
        self.format = self.formatter_class(self.stats)

    def configure(self, build: Build):
        self.stats.configure(build)
        return self