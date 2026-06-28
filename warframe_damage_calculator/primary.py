from dataclasses import dataclass

from .constants import DOT_MULTIPLIERS
from .dist import Dist
from .upgrade import Upgrade
from .ranged import Ranged

@dataclass
class Primary(Ranged):
    def _compute_moded_stats(self) -> None:
        super()._compute_moded_stats()

    def _compute_effective_stats(self) -> None:
        super()._compute_effective_stats()