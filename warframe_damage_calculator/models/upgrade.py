from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from ..utils import Value, ConditionEntry, RankEntry





class Upgrade:
    BOOLEAN_STATS = frozenset({"fire_rate_lock", "multishot_lock"})

    def __init__(self, stats: Mapping[str, Value] | None = None, conditional_stats: Mapping[str, ConditionEntry] | None = None, stacking_stats: Mapping[str, ConditionEntry] | None = None, rank_locked_stats: Mapping[str, RankEntry] | None = None, context: Mapping[str, Any] | None = None) -> None:
        self.stats = dict(stats or {})
        self.conditional_stats = dict(conditional_stats or {})
        self.stacking_stats = dict(stacking_stats or {})
        self.rank_locked_stats = dict(rank_locked_stats or {})
        self.context = dict(context or {})

    def copy(self) -> Upgrade:
        return deepcopy(self)

    @property
    def _label(self) -> str:
        return f" on upgrade {self.context['name']!r}" if self.context.get("name") else ""
