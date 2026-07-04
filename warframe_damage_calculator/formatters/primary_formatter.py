from __future__ import annotations

from typing import ClassVar

from ..calculators import PrimaryCalculator
from ..states.primary import PrimaryState
from .ranged_formatter import RangedFormatter


class PrimaryFormatter(RangedFormatter[PrimaryState]):
    calculator_class: ClassVar[type[PrimaryCalculator]] = PrimaryCalculator

    def __init__(self, base: PrimaryState) -> None:
        super().__init__(base)