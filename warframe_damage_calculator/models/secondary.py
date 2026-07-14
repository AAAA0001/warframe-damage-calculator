from ..calculators import SecondaryCalculator
from ..formatters import SecondaryFormatter
from .build import Build
from .record import Record
from .ranged import Ranged


class Secondary(Ranged):
    def __init__(self, stats=None, context=None):
        self.context = context.copy() if isinstance(context, Record) else Record(**(context or {}))
        self.context.category = "secondary"
        self.build = Build()
        self.stats = SecondaryCalculator(stats, self.context)
        self.format = SecondaryFormatter(self.stats)
