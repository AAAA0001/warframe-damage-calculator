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
        from ..calculators.upgrade_calculator import UpgradeCalculator

        names = {" ".join((upgrade.context.name or "").casefold().replace("_", " ").replace("-", " ").split()) for upgrade in self}
        context = Data(context)
        weapon = UpgradeCalculator._key(context.get("type") or context.get("weapon") or "")
        types = {weapon, UpgradeCalculator._key(context.get("category") or "")} - {""}
        if weapon == "bow": types.add("rifle")
        context.update({key: key in types for key in UpgradeCalculator.AUTOMATIC - {"sacrificial set"}})
        context.weapon = weapon
        context["sacrificial set"] = {"sacrificial pressure", "sacrificial steel"}.issubset(names)
        upgrades = [upgrade.copy() for upgrade in self]
        for upgrade in upgrades: upgrade.data.context = context | upgrade.context
        return Build(*(upgrade.resolve() for upgrade in upgrades))

    def aggregate(self):
        stats = Data()
        for upgrade in self:
            for stat, value in upgrade.stats.items():
                current = stats.get(stat)
                stats[stat] = value if current is None else current or value if isinstance(value, bool) else current + value
        return stats

    def get(self, stat, default=0): return self.aggregate().get(stat, default)
