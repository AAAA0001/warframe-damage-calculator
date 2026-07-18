from collections.abc import Mapping
from typing import Any, Self, overload

from ..calculators.weapon_calculator import WeaponCalculator
from ..formatters.weapon_formatter import WeaponFormatter
from .build import Build
from .data import Data
from .upgrade import Upgrade


class Weapon:
    calculator_type = WeaponCalculator
    formatter_type = WeaponFormatter

    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        values = Data({"stats": {}, "context": {}} | dict(data or {}))
        self.stats = values.stats
        self.context = values.context
        self.build = Build()
        self.results = self.calculator_type(self)
        self.format = self.formatter_type(self)

    @overload
    def configure(self, build: Build, /) -> Self: ...

    @overload
    def configure(self, *upgrades: Upgrade) -> Self: ...

    def configure(self, *args: Build | Upgrade) -> Self:
        if len(args) == 1 and isinstance(args[0], Build): build = args[0]
        elif all(isinstance(arg, Upgrade) for arg in args): build = Build(*args)
        else: raise TypeError("configure() accepts one Build or multiple Upgrade instances")
        self.build = build
        self.results.recompute()
        return self
