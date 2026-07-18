from ..calculators.melee_calculator import MeleeCalculator
from ..formatters.melee_formatter import MeleeFormatter
from .weapon import Weapon


class Melee(Weapon):
    calculator_type = MeleeCalculator
    formatter_type = MeleeFormatter
