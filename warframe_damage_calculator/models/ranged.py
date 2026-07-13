from ..calculators import RangedCalculator
from ..formatters import RangedFormatter
from .build import Build
from .weapon import Weapon


class Ranged(Weapon):
    def __init__(self, stats=None, context=None):
        self.context = {**dict(context or {}), "category": "ranged"}
        self.build = Build()
        self.stats = RangedCalculator(stats, self.context)
        self.format = RangedFormatter(self.stats)
