from ..calculators import SecondaryCalculator
from ..formatters import SecondaryFormatter
from .ranged import Ranged


class Secondary(Ranged):
    calculator_class = SecondaryCalculator
    formatter_class = SecondaryFormatter
    category = "secondary"
