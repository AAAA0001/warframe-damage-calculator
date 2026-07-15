from copy import deepcopy
from collections.abc import Mapping
from typing import Any

from .data import Data


class Upgrade:
    def __init__(self, data: Mapping[str, Any] | None = None, **legacy: Any) -> None:
        source = dict(data or {})
        source.update({key: value for key, value in legacy.items() if value is not None})
        source.setdefault("stats", {})
        source.setdefault("context", {})
        self.data = Data(source)
        self._organize_stats()

    def _organize_stats(self) -> None:
        normal, conditional, stacking, rank_locked = Data(), Data(), Data(), Data()
        for stat, effects in self.data.stats.items():
            entries = effects if isinstance(effects, list) else [effects]
            for raw in entries:
                is_effect = isinstance(raw, Mapping) and "value" in raw
                effect = Data(raw) if is_effect else Data({"value": raw})
                value, condition = effect.value, effect.when
                if condition is None:
                    normal[stat] = self._merge(normal.get(stat), value)
                elif isinstance(condition, Mapping) and condition.get("rank") is not None:
                    rank_locked[stat] = (value, condition["rank"])
                elif effect.stacking:
                    stacking[stat] = (value, condition)
                else:
                    conditional[stat] = (value, condition)
        self.data.stats = normal
        self.data.conditional_stats = conditional | self.data.get("conditional_stats", {})
        self.data.stacking_stats = stacking | self.data.get("stacking_stats", {})
        self.data.rank_locked_stats = rank_locked | self.data.get("rank_locked_stats", {})

    @staticmethod
    def _merge(current: Any, value: Any) -> Any:
        if current is None:
            return value
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            keys = current.keys() | value.keys()
            return Data({key: current.get(key, 0) + value.get(key, 0) for key in keys})
        if isinstance(value, bool):
            return current or value
        return current + value

    def __getattr__(self, name: str) -> Any:
        return getattr(self.data, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "data":
            object.__setattr__(self, name, value)
        else:
            setattr(self.data, name, value)

    def copy(self):
        return deepcopy(self)
