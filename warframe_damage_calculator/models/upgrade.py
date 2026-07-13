from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..utils import Condition, Stat, VALID_STATS, Value


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

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        for bucket_name in (
            "stats",
            "conditional_stats",
            "stacking_stats",
            "rank_locked_stats",
        ):
            bucket = getattr(self, bucket_name)
            unknown = sorted(
                (stat for stat in bucket if stat not in VALID_STATS),
                key=str,
            )
            if unknown:
                upgrade_name = self.name or "<unnamed>"
                unknown_names = ", ".join(repr(stat) for stat in unknown)
                raise ValueError(
                    f"Upgrade {upgrade_name!r} contains unknown stat(s) in "
                    f"{bucket_name}: {unknown_names}"
                )
