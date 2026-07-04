from dataclasses import dataclass

from .ranged_state import RangedState


@dataclass
class PrimaryState(RangedState):
    """Represents stats used by primary weapons.

    Adds primary-only values for Hunter Munitions, Primed Chamber, and the
    Vigilante bonus.

    ``PrimaryCalculator`` fills these values from the active ``Build`` and
    uses them while calculating critical chance, direct damage, and damage
    over time.

    Used by ``Primary`` weapons.
    """
    hunter_munitions: float = 0.0
    primed_chamber: float = 0.0
    vigilante_bonus: float = 0.0