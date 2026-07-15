from collections.abc import Mapping
from typing import Any

from ..calculators import SecondaryCalculator
from ..formatters import SecondaryFormatter
from .build import Build
from .data import Data
from .ranged import Ranged


class Secondary(Ranged):
    def __init__(self, data: Mapping[str, Any] | None = None):
        self.data = Data({"stats": {}, "context": {}} | dict(data or {}))
        self.build = Build()
        self.calculator = SecondaryCalculator(self.stats, self.context)
        self.format = SecondaryFormatter(self.calculator)
