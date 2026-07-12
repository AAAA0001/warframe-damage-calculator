from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..utils import Stat, Value, Condition


@dataclass(eq=False)
class Upgrade:
    name: str | None = None
    category: str | None = None
    compatibility: set[str] = field(default_factory=set)
    incompatibility: set[str] = field(default_factory=set)
    requirements: dict[str, object] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    max_rank: int | None = None
    max_stacks: int | None = None
    is_exilus: bool = False

    stats: dict[Stat, Value] = field(default_factory=dict)
    conditional_stats: dict[Stat, tuple[Value, Condition]] = field(default_factory=dict)
    stacking_stats: dict[Stat, tuple[Value, Condition]] = field(default_factory=dict)

    rank_locked_stats: dict[Stat, tuple[Value, int]] = field(default_factory=dict)
