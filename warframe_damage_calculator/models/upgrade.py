from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..utils import DAMAGE_TYPES
from .data import Data
from .dist import Dist


class Upgrade:
    AUTOMATIC = {"primary", "rifle", "bow", "shotgun", "sniper", "secondary", "pistol", "melee", "sacrificial set"}
    METADATA = {"name", "category", "type", "trigger", "is beam", "is battery", "compatibility", "incompatibility", "requirements", "max rank", "max stacks", "stacks", "is exilus", "rank", "weapon"}

    def __init__(self, data: Mapping[str, Any] | None = None):
        self.data = Data({"stats": {}, "context": {}} | dict(data or {}))

    def __getattr__(self, key):
        return getattr(self.data, key)

    @staticmethod
    def _normalize(value):
        return " ".join(str(value).casefold().replace("_", " ").replace("-", " ").split())

    def _count(self, value, field):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} on {self.context.get('name') or '<unnamed upgrade>'!r} must be a non-negative integer")
        return value

    @classmethod
    def _scale(cls, value, multiplier):
        if isinstance(value, Mapping): return {key: cls._scale(item, multiplier) for key, item in value.items()}
        return value if isinstance(value, bool) else value * multiplier

    @staticmethod
    def _add(stats, stat, value):
        if stat in DAMAGE_TYPES: stat, value = "damage", Dist({stat: value})
        elif stat == "damage" and not isinstance(value, Dist): value = Dist(value)
        current = stats.get(stat)
        stats[stat] = value if current is None else current or value if isinstance(value, bool) else current + value

    def resolve(self, context=None):
        shared = Data({self._normalize(key): value for key, value in (context or {}).items()})
        own = Data({self._normalize(key): value for key, value in self.context.items()})
        context = shared | own
        weapon_type = self._normalize(shared.get("type") or shared.get("weapon") or "")
        types = {weapon_type, self._normalize(shared.get("category") or "")} - {""}
        if weapon_type == "bow": types.add("rifle")
        context.update({condition: condition in types for condition in self.AUTOMATIC - {"sacrificial set"}})
        context.weapon = weapon_type
        defaults = not any(key not in self.AUTOMATIC | self.METADATA for key in context)
        max_rank = context.get("max rank")
        max_stacks = context.get("max stacks")
        max_rank = None if max_rank is None else self._count(max_rank, "max rank")
        max_stacks = None if max_stacks is None else self._count(max_stacks, "max stacks")
        rank = min(self._count(context.get("rank", max_rank or 0), "rank"), max_rank) if max_rank is not None else self._count(context.get("rank", 0), "rank")
        multiplier = 1 if max_rank in {None, 0} else (rank + 1) / (max_rank + 1)
        stats = Data()

        for stat, effects in self.stats.items():
            for effect in effects if isinstance(effects, list) else [effects]:
                effect = effect if isinstance(effect, Data) and "value" in effect else Data({"value": effect})
                value, condition = effect.value, effect.when
                if isinstance(condition, Mapping) and condition.get("rank") is not None:
                    if rank >= self._count(condition["rank"], "required rank"): self._add(stats, stat, value)
                    continue
                if condition is not None:
                    condition = self._normalize(condition)
                    if effect.stacking:
                        stacks = self._count(context.get(condition, context.get("stacks", (max_stacks or 0) if defaults else 0)), condition)
                        stacks = min(stacks, max_stacks) if max_stacks is not None else stacks
                        if not stacks: continue
                        value = self._scale(value, multiplier)
                        self._add(stats, stat, value if isinstance(value, bool) else value * stacks)
                        continue
                    if not context.get(condition, False if condition in self.AUTOMATIC else defaults): continue
                self._add(stats, stat, self._scale(value, multiplier))

        context.rank = rank
        return Upgrade({"stats": stats, "context": context})

    def copy(self):
        return Upgrade(self.data)
