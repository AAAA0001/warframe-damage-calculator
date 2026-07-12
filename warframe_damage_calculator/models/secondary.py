from __future__ import annotations

from typing import Unpack

from ..calculators import SecondaryCalculator
from ..formatters import SecondaryFormatter
from ..fields import SecondaryFields
from ..states import SecondaryState
from .ranged import Ranged
from .weapon import _state_kwargs


class Secondary(Ranged):
    def __init__(self, **kwargs: Unpack[SecondaryFields]) -> None:
        base = SecondaryState(**_state_kwargs(kwargs, ranged=True))
        self.stats: SecondaryCalculator = SecondaryCalculator(base)
        self.format: SecondaryFormatter = SecondaryFormatter(self.stats)
