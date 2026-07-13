from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..calculators import SecondaryCalculator
from ..formatters import SecondaryFormatter
from .build import Build
from .ranged import Ranged


class Secondary(Ranged):
    def __init__(self, stats: Mapping[str, Any] | None = None, context: Mapping[str, Any] | None = None) -> None:
        self.context = {**dict(context or {}), "category": "secondary"}
        self.build = Build()
        self.stats = SecondaryCalculator(stats, self.context)
        self.format = SecondaryFormatter(self.stats)
