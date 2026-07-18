from ..calculators.ranged_calculator import RangedCalculator
from ..formatters.ranged_formatter import RangedFormatter
from .data import RangedData
from .weapon import Weapon


class Ranged(Weapon):
    data_type = RangedData
    calculator_type = RangedCalculator
    formatter_type = RangedFormatter
