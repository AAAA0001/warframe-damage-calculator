from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..utils import Value
from ..calculators import PrimaryCalculator
from ..formatters import PrimaryFormatter
from .build import Build
from .ranged import Ranged


class Primary(Ranged):
    def __init__(self, stats: Mapping[str, Value] | None = None, context: Mapping[str, Any] | None = None) -> None:
        self.context = {**dict(context or {}), "category": "primary"}
        self.build = Build()
        self.stats = PrimaryCalculator(stats, self.context)
        self.format = PrimaryFormatter(self.stats)
