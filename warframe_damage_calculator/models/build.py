from .record import Record
from .upgrade import Upgrade


class Build:
    def __init__(self, *upgrades):
        self.upgrades = list(upgrades)

    def __add__(self, other):
        if isinstance(other, Upgrade):
            return Build(*self.upgrades, other)
        if isinstance(other, Build):
            return Build(*self.upgrades, *other.upgrades)
        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, Upgrade):
            return Build(other, *self.upgrades)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Upgrade):
            excluded = {other}
        elif isinstance(other, Build):
            excluded = set(other.upgrades)
        else:
            return NotImplemented
        return Build(*(upgrade for upgrade in self.upgrades if upgrade not in excluded))

    def __iter__(self):
        return iter(self.upgrades)

    def contextualize(self, context, copy=False):
        build = Build(*(upgrade.copy() for upgrade in self)) if copy else self
        shared = context if isinstance(context, Record) else Record(**(context or {}))
        for upgrade in build:
            upgrade.context = shared | upgrade.context
        return build

    def aggregate(self):
        stats = Record()
        for upgrade in self:
            for stat, value in upgrade.stats.items():
                current = stats.get(stat)
                setattr(stats, stat, value if current is None else current or value if isinstance(value, bool) else current + value)
        return stats

    def get(self, stat, default=0):
        return self.aggregate().get(stat, default)
