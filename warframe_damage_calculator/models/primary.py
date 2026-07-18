from ..calculators.primary_calculator import PrimaryCalculator
from ..formatters.primary_formatter import PrimaryFormatter
from .ranged import Ranged


class Primary(Ranged):
    calculator_type = PrimaryCalculator
    formatter_type = PrimaryFormatter
