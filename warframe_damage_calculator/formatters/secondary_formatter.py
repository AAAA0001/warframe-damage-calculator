from __future__ import annotations

from ..calculators import SecondaryCalculator
from ..states import SecondaryState
from .ranged_formatter import RangedFormatter


class SecondaryFormatter(RangedFormatter[SecondaryState]):
    """Formatter for secondary weapon stats.

    Secondary weapons use the same summary layout as other ranged weapons.

    Connects ``RangedFormatter`` to ``SecondaryCalculator`` so ``Secondary``
    models can expose formatted output through ``format``.
    """
    def __init__(self, calculator: SecondaryCalculator) -> None:
        super().__init__(calculator)