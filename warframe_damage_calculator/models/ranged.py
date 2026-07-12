from __future__ import annotations

from typing import Unpack

from ..calculators import RangedCalculator
from ..formatters import RangedFormatter
from ..fields import RangedFields
from ..states import RangedState
from .weapon import Weapon, _state_kwargs


class Ranged(Weapon):
    def __init__(self, **kwargs: Unpack[RangedFields]) -> None:
        base = RangedState(**_state_kwargs(kwargs, ranged=True))
        self.stats: RangedCalculator = RangedCalculator(base)
        self.format: RangedFormatter = RangedFormatter(self.stats)

