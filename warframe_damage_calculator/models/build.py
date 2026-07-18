from collections.abc import Iterator
from typing import Self

from ..calculators.build_calculator import BuildCalculator
from .upgrade import Upgrade


class Build:
    def __init__(self, *upgrades: Upgrade) -> None:
        self.upgrades = [Upgrade({"stats": upgrade.stats.copy(), "context": upgrade.context.copy()}) for upgrade in upgrades]
        self.results = BuildCalculator(self)

    def __iter__(self) -> Iterator[Upgrade]:
        return iter(self.upgrades)

    def __len__(self) -> int:
        return len(self.upgrades)

    def __add__(self, other: Self | Upgrade) -> Self:
        return Build(*self, other) if isinstance(other, Upgrade) else Build(*self, *other)

    def __radd__(self, other: Upgrade) -> Self:
        return Build(other, *self)

    def __sub__(self, other: Self | Upgrade) -> Self:
        excluded = [(other.stats, other.context)] if isinstance(other, Upgrade) else [(upgrade.stats, upgrade.context) for upgrade in other]
        return Build(*(upgrade for upgrade in self if (upgrade.stats, upgrade.context) not in excluded))
