from __future__ import annotations

from typing import Any

from ..utils import Condition, Stat, VALID_STATS, Value


class Upgrade:
    def __init__(self, stats: dict[Stat, Value] | None = None, conditional_stats: dict[Stat, list[Value | Condition]] | None = None, stacking_stats: dict[Stat, list[Value | Condition]] | None = None, rank_locked_stats: dict[Stat, list[Value | int]] | None = None, context: dict[str, Any] | None = None) -> None:
        self.stats = stats or {}
        self.conditional_stats = conditional_stats or {}
        self.stacking_stats = stacking_stats or {}
        self.rank_locked_stats = rank_locked_stats or {}
        self.context = context or {}
        self.validate()

    def copy(self, **changes: Any) -> Upgrade:
        return Upgrade(**{"stats": self.stats, "conditional_stats": self.conditional_stats, "stacking_stats": self.stacking_stats, "rank_locked_stats": self.rank_locked_stats, "context": self.context, **changes})

    def validate(self) -> None:
        for bucket_name in ("stats", "conditional_stats", "stacking_stats", "rank_locked_stats"):
            bucket = getattr(self, bucket_name)
            unknown = sorted((stat for stat in bucket if stat not in VALID_STATS), key=str)
            if unknown:
                upgrade_name = self.context.get("name") or "<unnamed>"
                unknown_names = ", ".join(repr(stat) for stat in unknown)
                raise ValueError(f"Upgrade {upgrade_name!r} contains unknown stat(s) in {bucket_name}: {unknown_names}")
