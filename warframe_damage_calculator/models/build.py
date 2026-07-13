from __future__ import annotations

from collections.abc import Mapping
from typing import Iterator, Self

from ..utils import Stat, Value
from .upgrade import Upgrade


class Build:
    def __init__(self, *upgrades: Upgrade) -> None:
        if any(not isinstance(upgrade, Upgrade) for upgrade in upgrades):
            raise TypeError("Build only accepts Upgrade objects")
        self.upgrades = list(upgrades)

    def __add__(self, other: Upgrade | Build) -> Build:
        if isinstance(other, Upgrade):
            return Build(*self.upgrades, other)
        if isinstance(other, Build):
            return Build(*self.upgrades, *other.upgrades)
        return NotImplemented

    def __radd__(self, other: Upgrade) -> Build:
        if isinstance(other, Upgrade):
            return Build(other, *self.upgrades)
        return NotImplemented

    def __sub__(self, other: Upgrade | Build) -> Build:
        if isinstance(other, Upgrade):
            excluded = {other}
        elif isinstance(other, Build):
            excluded = set(other.upgrades)
        else:
            return NotImplemented
        return Build(*(upgrade for upgrade in self.upgrades if upgrade not in excluded))

    def __iter__(self) -> Iterator[Upgrade]:
        return iter(self.upgrades)

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().replace("_", " ").replace("-", " ").split())

    def contextualize(self, context: Mapping[str, object], copy: bool = False) -> Self:
        build = Build(*(upgrade.copy(context=dict(upgrade.context)) for upgrade in self)) if copy else self
        names = {self._normalize(str(upgrade.context.get("name") or "")) for upgrade in build}
        shared_context = dict(context)
        shared_context["sacrificial set"] = {"sacrificial pressure", "sacrificial steel"}.issubset(names)
        for upgrade in build:
            upgrade.context = {**shared_context, **upgrade.context}
        return build

    def aggregate(self) -> dict[Stat, Value]:
        stats: dict[Stat, Value] = {}
        for upgrade in self:
            for stat, value in upgrade.stats.items():
                current = stats.get(stat)
                if current is None:
                    stats[stat] = value
                elif isinstance(current, bool) and isinstance(value, bool):
                    stats[stat] = current or value
                elif isinstance(current, bool) or isinstance(value, bool):
                    raise TypeError(f"Cannot combine values for build stat {stat!r}")
                else:
                    try:
                        stats[stat] = current + value
                    except TypeError:
                        raise TypeError(f"Cannot combine values for build stat {stat!r}") from None
        return stats

    def get(self, stat: Stat, default: Value = 0) -> Value:
        return self.aggregate().get(stat, default)

