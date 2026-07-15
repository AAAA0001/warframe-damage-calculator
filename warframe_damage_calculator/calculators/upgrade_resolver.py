from collections.abc import Mapping

from ..utils import DAMAGE_TYPES
from ..models import Dist, Build
from ..models.record import Record


class UpgradeResolver:
    METADATA = {"name", "category", "type", "trigger", "is beam", "is battery", "compatibility", "incompatibility", "requirements", "max rank", "max stacks", "stacks", "is exilus"}
    AUTOMATIC_CONDITIONS = {"primary", "rifle", "bow", "shotgun", "sniper", "secondary", "pistol", "melee", "sacrificial set"}

    def __init__(self, weapon_context):
        self.weapon_context = weapon_context

    @property
    def context(self):
        context = Record(**{self._normalize(key): value for key, value in self.weapon_context.items()})
        weapon_type = self._normalize(self.weapon_context.get("type") or "")
        weapon_types = {weapon_type, self._normalize(self.weapon_context.get("category") or "")} - {""}
        if weapon_type == "bow":
            weapon_types.add("rifle")
        context.update({name: name in weapon_types for name in self.AUTOMATIC_CONDITIONS - {"sacrificial set"}})
        context.weapon = weapon_type
        return context

    @staticmethod
    def _normalize(value):
        return " ".join(str(value).casefold().replace("_", " ").replace("-", " ").split())

    @staticmethod
    def _count(value, field, upgrade):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            name = upgrade.context.get("name") or "<unnamed upgrade>"
            raise ValueError(f"{field} on {name!r} must be a non-negative integer")
        return value

    @staticmethod
    def _scale(value, multiplier):
        if isinstance(value, Mapping):
            return {key: UpgradeResolver._scale(item, multiplier) for key, item in value.items()}
        return value if isinstance(value, bool) else value * multiplier

    @staticmethod
    def _merge(target, stat, value):
        if stat in DAMAGE_TYPES:
            value = Dist({stat: value})
            stat = "damage"
        elif stat == "damage" and not isinstance(value, Dist):
            value = Dist(value)
        current = target.get(stat)
        setattr(target, stat, value if current is None else current or value if isinstance(value, bool) else current + value)

    def _limit(self, context, field, upgrade):
        value = context.get(field)
        return None if value is None else self._count(value, field, upgrade)

    def resolve(self, build):
        names = {self._normalize(upgrade.context.get("name") or "") for upgrade in build}
        shared_context = self.context | Record(**{"sacrificial set": {"sacrificial pressure", "sacrificial steel"}.issubset(names)})
        resolved = []

        for source in build:
            upgrade = source.copy()
            context = Record(**{self._normalize(key): value for key, value in upgrade.context.items()}) | shared_context
            use_defaults = not any(key not in self.AUTOMATIC_CONDITIONS | self.METADATA | {"rank", "weapon"} for key in context)
            max_rank = self._limit(context, "max rank", upgrade)
            max_stacks = self._limit(context, "max stacks", upgrade)
            rank = self._count(context.get("rank", max_rank or 0), "rank", upgrade)
            if max_rank is not None:
                rank = min(rank, max_rank)
            multiplier = 1.0 if max_rank in {None, 0} else (rank + 1) / (max_rank + 1)
            stats = Record()

            for stat, value in upgrade.stats.items():
                self._merge(stats, stat, self._scale(value, multiplier))

            for stat, (value, required_rank) in upgrade.rank_locked_stats.items():
                if rank >= self._count(required_rank, "required rank", upgrade):
                    self._merge(stats, stat, value)

            for stat, (value, condition) in upgrade.conditional_stats.items():
                condition = self._normalize(condition)
                default = False if condition in self.AUTOMATIC_CONDITIONS else use_defaults
                if context.get(condition, default):
                    self._merge(stats, stat, self._scale(value, multiplier))

            for stat, (value, condition) in upgrade.stacking_stats.items():
                condition = self._normalize(condition)
                default_stacks = context.get("stacks", (max_stacks or 0) if use_defaults else 0)
                stacks = self._count(context.get(condition, default_stacks), condition, upgrade)
                if max_stacks is not None:
                    stacks = min(stacks, max_stacks)
                if stacks:
                    stacked_value = self._scale(value, multiplier)
                    value = stacked_value if isinstance(stacked_value, bool) else stacked_value * stacks
                    self._merge(stats, stat, value)

            upgrade.context.rank = rank
            upgrade.stats = stats
            upgrade.rank_locked_stats = Record()
            upgrade.conditional_stats = Record()
            upgrade.stacking_stats = Record()
            resolved.append(upgrade)

        return Build(*resolved)
