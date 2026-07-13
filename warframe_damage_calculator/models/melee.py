from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..calculators import MeleeCalculator
from ..formatters import MeleeFormatter
from .build import Build
from .weapon import Weapon


class Melee(Weapon):
    def __init__(self, stats: Mapping[str, Any] | None = None, context: Mapping[str, Any] | None = None) -> None:
        self.context = {**dict(context or {}), "category": "melee"}
        self.build = Build()
        self.stats = MeleeCalculator(stats, self.context)
        self.format = MeleeFormatter(self.stats)
