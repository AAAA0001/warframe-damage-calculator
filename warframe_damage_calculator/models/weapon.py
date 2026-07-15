from collections.abc import Mapping
from typing import Any

from ..calculators import WeaponCalculator
from ..formatters import WeaponFormatter
from .build import Build
from .data import Data


class Weapon:
    calculator_class = WeaponCalculator
    formatter_class = WeaponFormatter
    category = "weapon"

    def __init__(self, data: Mapping[str, Any] | None = None, **legacy: Any) -> None:
        source = dict(data or {})
        source.update({key: value for key, value in legacy.items() if value is not None})
        source.setdefault("stats", {})
        source.setdefault("context", {})
        self.data = Data(source)
        self.data.context.category = self.category
        self.build = Build()
        self.calculator = self.calculator_class(self.stats, self.context)
        self.format = self.formatter_class(self.calculator)

    @property
    def stats(self):
        return self.data.stats

    @property
    def context(self):
        return self.data.context

    def configure(self, *upgrades):
        build = upgrades[0] if len(upgrades) == 1 and isinstance(upgrades[0], Build) else Build(*upgrades)
        self.build = Build(*(upgrade.copy() for upgrade in build))
        self.calculator.set_build(self.build)
        return self
