from __future__ import annotations

from typing import Unpack

from ..calculators import PrimaryCalculator
from ..formatters import PrimaryFormatter
from ..fields import PrimaryField
from ..states import PrimaryState
from .ranged import Ranged


class Primary(Ranged):
    """Represents a primary weapon that can be configured and calculated.

    Primary weapons use the ranged weapon inputs, then add primary-specific
    calculations through ``PrimaryCalculator``.

    Mechanics such as Hunter Munitions, Primed Chamber, and Vigilante bonuses
    come from the active ``Build`` and are handled during calculation.

    Use this class when evaluating a primary weapon build.
    """
    _state_class = PrimaryState
    _calculator_class = PrimaryCalculator
    _formatter_class = PrimaryFormatter

    def __init__(self, **kwargs: Unpack[PrimaryField]) -> None:
        super().__init__(**kwargs)

    

    
    