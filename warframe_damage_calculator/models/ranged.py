from ..calculators.ranged_calculator import RangedCalculator
from ..formatters.ranged_formatter import RangedFormatter
from .weapon import Weapon


class Ranged(Weapon):
    calculator_type = RangedCalculator
    formatter_type = RangedFormatter
