from copy import deepcopy

from .record import Record


class Upgrade:
    def __init__(self, stats=None, conditional_stats=None, stacking_stats=None, rank_locked_stats=None, context=None):
        self.stats = stats.copy() if isinstance(stats, Record) else Record(**(stats or {}))
        self.conditional_stats = conditional_stats.copy() if isinstance(conditional_stats, Record) else Record(**(conditional_stats or {}))
        self.stacking_stats = stacking_stats.copy() if isinstance(stacking_stats, Record) else Record(**(stacking_stats or {}))
        self.rank_locked_stats = rank_locked_stats.copy() if isinstance(rank_locked_stats, Record) else Record(**(rank_locked_stats or {}))
        self.context = context.copy() if isinstance(context, Record) else Record(**(context or {}))

    def copy(self):
        return deepcopy(self)
