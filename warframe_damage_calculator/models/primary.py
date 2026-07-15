from ..calculators import PrimaryCalculator
from ..formatters import PrimaryFormatter
from .ranged import Ranged


class Primary(Ranged):
    calculator_class = PrimaryCalculator
    formatter_class = PrimaryFormatter
    category = "primary"
