from __future__ import annotations

from ..calculators import RangedCalculator
from ..formatters import RangedFormatter
from ..states.ranged import RangedState
from .weapon import Weapon


class Ranged(Weapon):
    calculator_class = RangedCalculator
    formatter_class = RangedFormatter

    def __init__(self, base: RangedState) -> None:
        super().__init__(base)

