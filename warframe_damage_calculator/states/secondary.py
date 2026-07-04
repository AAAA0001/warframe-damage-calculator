from dataclasses import dataclass

from .ranged import RangedState


@dataclass
class SecondaryState(RangedState):
    secondary_enervate: int = 0
    secondary_encumber: float = 0.0