from ..calculators import MeleeCalculator
from ..formatters import MeleeFormatter
from .weapon import Weapon


class Melee(Weapon):
    calculator_class = MeleeCalculator
    formatter_class = MeleeFormatter
    category = "melee"
