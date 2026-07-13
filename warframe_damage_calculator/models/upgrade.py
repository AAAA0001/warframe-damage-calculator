from copy import deepcopy

class Upgrade:
    def __init__(self, stats=None, conditional_stats=None, stacking_stats=None, rank_locked_stats=None, context=None):
        self.stats = dict(stats or {})
        self.conditional_stats = dict(conditional_stats or {})
        self.stacking_stats = dict(stacking_stats or {})
        self.rank_locked_stats = dict(rank_locked_stats or {})
        self.context = dict(context or {})

    def copy(self):
        return deepcopy(self)
