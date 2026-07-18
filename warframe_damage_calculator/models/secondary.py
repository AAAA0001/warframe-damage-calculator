from ..calculators.secondary_calculator import SecondaryCalculator
from ..formatters.secondary_formatter import SecondaryFormatter
from .ranged import Ranged


class Secondary(Ranged):
    calculator_type = SecondaryCalculator
    formatter_type = SecondaryFormatter
