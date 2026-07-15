from ..calculators import RangedCalculator
from ..formatters import RangedFormatter
from .weapon import Weapon


class Ranged(Weapon):
    calculator_class = RangedCalculator
    formatter_class = RangedFormatter
    category = "ranged"
