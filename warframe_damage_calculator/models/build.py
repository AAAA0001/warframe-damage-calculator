from __future__ import annotations

from .data import Data
from .upgrade import Upgrade


class Build:
    def __init__(self, *upgrades): self.upgrades = list(upgrades)
    def __iter__(self): return iter(self.upgrades)
    def __add__(self, other): return Build(*self, other) if isinstance(other, Upgrade) else Build(*self, *other)
    def __radd__(self, other): return Build(other, *self)

    def __sub__(self, other):
        excluded = {other} if isinstance(other, Upgrade) else set(other)
        return Build(*(upgrade for upgrade in self if upgrade not in excluded))

    def resolve(self, context=None):
        names = {Upgrade._normalize(upgrade.context.name or "") for upgrade in self}
        context = Data(context)
        context["sacrificial set"] = {"sacrificial pressure", "sacrificial steel"}.issubset(names)
        return Build(*(upgrade.resolve(context) for upgrade in self))

    def aggregate(self):
        stats = Data()
        for upgrade in self:
            for stat, value in upgrade.stats.items():
                current = stats.get(stat)
                stats[stat] = value if current is None else current or value if isinstance(value, bool) else current + value
        return stats

    def get(self, stat, default=0): return self.aggregate().get(stat, default)
