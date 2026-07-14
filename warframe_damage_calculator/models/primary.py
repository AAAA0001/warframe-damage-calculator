from ..calculators import PrimaryCalculator
from ..formatters import PrimaryFormatter
from .build import Build
from .record import Record
from .ranged import Ranged


class Primary(Ranged):
    def __init__(self, stats=None, context=None):
        self.context = context.copy() if isinstance(context, Record) else Record(**(context or {}))
        self.context.category = "primary"
        self.build = Build()
        self.stats = PrimaryCalculator(stats, self.context)
        self.format = PrimaryFormatter(self.stats)
