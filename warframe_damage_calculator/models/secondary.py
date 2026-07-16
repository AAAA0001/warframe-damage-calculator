from collections.abc import Mapping
from typing import Any

from .data import Data
from .build import Build
from .ranged import Ranged
from ..calculators.secondary_calculator import SecondaryCalculator
from ..formatters.secondary_formatter import SecondaryFormatter


class Secondary(Ranged):
    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        self.data = Data({"stats": {}, "context": {}} | dict(data or {}))
        self.build = Build()
        self.stats = SecondaryCalculator(self.data)
        self.format = SecondaryFormatter(self.stats)
