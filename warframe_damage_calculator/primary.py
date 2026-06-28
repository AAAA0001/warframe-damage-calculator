from dataclasses import dataclass

from .constants import DOT_MULTIPLIERS
from .dist import Dist
from .upgrade import Upgrade
from .ranged import Ranged

@dataclass
class Primary(Ranged):
    pass
