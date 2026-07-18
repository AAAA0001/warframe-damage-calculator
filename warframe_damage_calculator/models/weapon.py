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
        self.data = Data({"stats": {}, "context": {}} | dict(data or {}))
        self.stats = self.calculator_type(self.data)
        self.format = self.formatter_type(self.stats)

    @overload
    def configure(self, build: Build, /) -> Self: ...

    @overload
    def configure(self, *upgrades: Upgrade) -> Self: ...

    def configure(self, *args: Build | Upgrade) -> Self:
        if len(args) == 1 and isinstance(args[0], Build): build = args[0]
        elif all(isinstance(arg, Upgrade) for arg in args): build = Build(*args)
        else: raise TypeError("configure() accepts one Build or multiple Upgrade instances")
        self.stats.set_build(build)
        return self
