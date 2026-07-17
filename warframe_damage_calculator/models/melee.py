from typing import Any

from .data import Data
from .build import Build
from .weapon import Weapon
from ..calculators.melee_calculator import MeleeCalculator
from ..formatters.melee_formatter import MeleeFormatter


class Melee(Weapon):
    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.data = Data({"stats": {}, "context": {}} | (data or {}))
        self.build = Build()
        self.stats = MeleeCalculator(self.data)
        self.format = MeleeFormatter(self.stats)
