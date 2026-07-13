from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..utils import Value
from ..calculators import RangedCalculator
from ..formatters import RangedFormatter
from .build import Build
from .weapon import Weapon


class Ranged(Weapon):
    def __init__(self, stats: Mapping[str, Value] | None = None, context: Mapping[str, Any] | None = None) -> None:
        self.context = {**dict(context or {}), "category": "ranged"}
        self.build = Build()
        self.stats = RangedCalculator(stats, self.context)
        self.format = RangedFormatter(self.stats)

