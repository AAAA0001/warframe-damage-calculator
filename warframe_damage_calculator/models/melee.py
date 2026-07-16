from collections.abc import Mapping
from typing import Any

from ..calculators import MeleeCalculator
from ..formatters import MeleeFormatter
from .build import Build
from .data import Data
from .weapon import Weapon


class Melee(Weapon):
    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        self.data = Data({"stats": {}, "context": {}} | dict(data or {}))
        self.build = Build()
        self.stats = MeleeCalculator(self.data)
        self.format = MeleeFormatter(self.stats)
