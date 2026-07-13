from ..calculators import MeleeCalculator
from ..formatters import MeleeFormatter
from .build import Build
from .weapon import Weapon


class Melee(Weapon):
    def __init__(self, stats=None, context=None):
        self.context = {**dict(context or {}), "category": "melee"}
        self.build = Build()
        self.stats = MeleeCalculator(stats, self.context)
        self.format = MeleeFormatter(self.stats)
