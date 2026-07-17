from typing import Any

from .data import Data
from .build import Build
from .weapon import Weapon
from ..calculators.ranged_calculator import RangedCalculator
from ..formatters.ranged_formatter import RangedFormatter


class Ranged(Weapon):
    def __init__(self, data: dict[str, Any] | None = None):
        self.data = Data({"stats": {}, "context": {}} | (data or {}))
        self.build = Build()
        self.stats = RangedCalculator(self.data)
        self.format = RangedFormatter(self.stats)
