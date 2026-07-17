from typing import Any

from .data import Data
from .build import Build
from .ranged import Ranged
from ..calculators.primary_calculator import PrimaryCalculator
from ..formatters.primary_formatter import PrimaryFormatter


class Primary(Ranged):
    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.data = Data({"stats": {}, "context": {}} | (data or {}))
        self.build = Build()
        self.stats = PrimaryCalculator(self.data)
        self.format = PrimaryFormatter(self.stats)
