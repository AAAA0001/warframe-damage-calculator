from ..calculators import RangedCalculator
from ..formatters import RangedFormatter
from .build import Build
from .record import Record
from .weapon import Weapon


class Ranged(Weapon):
    def __init__(self, stats=None, context=None):
        self.context = context.copy() if isinstance(context, Record) else Record(**(context or {}))
        self.context.category = "ranged"
        self.build = Build()
        self.stats = RangedCalculator(stats, self.context)
        self.format = RangedFormatter(self.stats)
