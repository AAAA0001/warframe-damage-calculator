from ..calculators import WeaponCalculator
from ..formatters import WeaponFormatter
from .build import Build
from .record import Record


class Weapon:
    def __init__(self, stats=None, context=None):
        self.context = context.copy() if isinstance(context, Record) else Record(**(context or {}))
        self.context.category = "weapon"
        self.build = Build()
        self.stats = WeaponCalculator(stats, self.context)
        self.format = WeaponFormatter(self.stats)

    def configure(self, *upgrades):
        build = upgrades[0] if len(upgrades) == 1 and isinstance(upgrades[0], Build) else Build(*upgrades)
        self.build = Build(*(upgrade.copy() for upgrade in build))
        self.stats.set_build(self.build)
        return self
