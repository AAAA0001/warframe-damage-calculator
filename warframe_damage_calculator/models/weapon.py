from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self

from ..utils import Value
from ..calculators import WeaponCalculator
from ..formatters import WeaponFormatter
from .upgrade import Upgrade
from .build import Build


class Weapon:
    def __init__(self, stats: Mapping[str, Value] | None = None, context: Mapping[str, Any] | None = None) -> None:
        self.context = {**dict(context or {}), "category": "weapon"}
        self.build = Build()
        self.stats = WeaponCalculator(stats, self.context)
        self.format = WeaponFormatter(self.stats)

    def configure(self, *upgrades: Build | Upgrade) -> Self:
        if len(upgrades) == 1 and isinstance(upgrades[0], Build):
            build = upgrades[0]
        elif all(isinstance(upgrade, Upgrade) for upgrade in upgrades):
            build = Build(*upgrades)
        else:
            raise TypeError("configure() accepts Upgrade objects or one Build")
        self.build = Build(*(upgrade.copy() for upgrade in build))
        self.stats.set_build(self.build)
        return self
