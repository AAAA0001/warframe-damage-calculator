from collections.abc import Mapping
from typing import Any

from ..calculators import PrimaryCalculator
from ..formatters import PrimaryFormatter
from .build import Build
from .data import Data
from .ranged import Ranged


class Primary(Ranged):
    def __init__(self, data: Mapping[str, Any] | None = None):
        self.data = Data({"stats": {}, "context": {}} | dict(data or {}))
        self.build = Build()
        self.calculator = PrimaryCalculator(self.stats, self.context)
        self.format = PrimaryFormatter(self.calculator)
