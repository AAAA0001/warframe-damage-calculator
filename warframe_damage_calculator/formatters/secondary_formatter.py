from __future__ import annotations

from typing import ClassVar

from ..calculators import SecondaryCalculator
from ..states.secondary import SecondaryState
from .ranged_formatter import RangedFormatter


class SecondaryFormatter(RangedFormatter[SecondaryState]):
    calculator_class: ClassVar[type[SecondaryCalculator]] = SecondaryCalculator
    
    def __init__(self, base: SecondaryState) -> None:
        super().__init__(base)