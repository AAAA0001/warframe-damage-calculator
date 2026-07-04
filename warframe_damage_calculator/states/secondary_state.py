from dataclasses import dataclass

from .ranged_state import RangedState


@dataclass
class SecondaryState(RangedState):
    """Represents stats used by secondary weapons.

    Adds secondary-only values for Secondary Enervate and Secondary Encumber.

    ``SecondaryCalculator`` fills these values from the active ``Build`` and
    uses them while calculating critical bonuses and damage over time.

    Used by ``Secondary`` weapons.
    """
    secondary_enervate: int = 0
    secondary_encumber: float = 0.0