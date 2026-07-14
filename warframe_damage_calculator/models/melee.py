from ..calculators import MeleeCalculator
from ..formatters import MeleeFormatter
from .build import Build
from .record import Record
from .weapon import Weapon


class Melee(Weapon):
    def __init__(self, stats=None, context=None):
        self.context = context.copy() if isinstance(context, Record) else Record(**(context or {}))
        self.context.category = "melee"
        self.build = Build()
        self.stats = MeleeCalculator(stats, self.context)
        self.format = MeleeFormatter(self.stats)
