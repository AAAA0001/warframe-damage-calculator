from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

from ..utils import UpgradeStat
from .dist import dist


StatValue: TypeAlias = float | int | bool | dist


@dataclass(eq=False)
class Upgrade:
    name: str | None = None
    category: str | None = None
    compatibility: set[str] = field(default_factory=set)
    incompatibility: set[str] = field(default_factory=set)
    requirements: dict[str, object] = field(default_factory=dict)
    max_rank: int | None = None
    max_stacks: int | None = None
    is_exilus: bool = False

    stats: dict[UpgradeStat, StatValue] = field(default_factory=dict)
    conditional_stats: dict[UpgradeStat, tuple[StatValue, str]] = field(default_factory=dict)
    stacking_stats: dict[UpgradeStat, tuple[StatValue, str]] = field(default_factory=dict)
