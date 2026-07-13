from ..utils import DAMAGE_TYPES
from ..models import Build, dist


class UpgradeResolver:
    METADATA = {"name", "category", "type", "trigger", "is beam", "is battery", "compatibility", "incompatibility", "requirements", "max rank", "max stacks", "is exilus"}
    AUTOMATIC_CONDITIONS = {"primary", "rifle", "bow", "shotgun", "sniper", "secondary", "pistol", "melee", "sacrificial set"}

    def __init__(self, weapon_context):
        self.weapon_context = weapon_context

    @staticmethod
    def _normalize(value):
        return " ".join(value.casefold().replace("_", " ").replace("-", " ").split())

    @property
    def context(self):
        context = {self._normalize(key): value for key, value in self.weapon_context.items()}
        weapon_type = self._normalize(str(self.weapon_context.get("type") or ""))
        weapon_types = {weapon_type} if weapon_type else set()
        category = self._normalize(str(self.weapon_context.get("category") or ""))
        if category:
            weapon_types.add(category)

        if weapon_type == "bow":
            weapon_types.add("rifle")

        context.update({name: name in weapon_types for name in self.AUTOMATIC_CONDITIONS if name != "sacrificial set"})
        context["weapon"] = weapon_type
        return context

    def _resolve_context(self, upgrade, shared_context):
        context = {**{self._normalize(key): value for key, value in upgrade.context.items()}, **shared_context}
        context.setdefault("rank", context.get("max rank") or 0)
        return context

    def _condition_active(self, condition, context, use_defaults):
        condition = self._normalize(condition)
        default = False if condition in self.AUTOMATIC_CONDITIONS else use_defaults
        return bool(context.get(condition, default))

    @staticmethod
    def _scale(value, multiplier):
        return value if isinstance(value, bool) else value * multiplier

    @staticmethod
    def _merge(target, stat, value):
        if stat in DAMAGE_TYPES:
            value = dist({stat: value})
            stat = "damage"
        current = target.get(stat)
        target[stat] = value if current is None else current or value if isinstance(value, bool) else current + value

    def resolve(self, build):
        names = {self._normalize(str(upgrade.context.get("name") or "")) for upgrade in build}
        shared_context = {**self.context, "sacrificial set": {"sacrificial pressure", "sacrificial steel"}.issubset(names)}
        resolved_upgrades = []

        for source in build:
            upgrade = source.copy()
            context = self._resolve_context(upgrade, shared_context)
            use_defaults = not any(key not in self.AUTOMATIC_CONDITIONS | self.METADATA | {"rank", "weapon"} for key in context)
            resolved = {}
            max_rank = context.get("max rank")
            max_stacks = context.get("max stacks")
            rank = context.get("rank", 0)
            if max_rank is not None:
                rank = min(rank, max_rank)
                context["rank"] = rank
            multiplier = 1.0 if max_rank in {None, 0} else (rank + 1) / (max_rank + 1)

            for stat, value in upgrade.stats.items():
                self._merge(resolved, stat, self._scale(value, multiplier))

            for stat, (value, required_rank) in upgrade.rank_locked_stats.items():
                if rank >= required_rank:
                    self._merge(resolved, stat, value)

            for stat, (value, condition) in upgrade.conditional_stats.items():
                if self._condition_active(condition, context, use_defaults):
                    self._merge(resolved, stat, self._scale(value, multiplier))

            for stat, (value, condition) in upgrade.stacking_stats.items():
                normalized_condition = self._normalize(condition)
                stack_count = context.get(normalized_condition, (max_stacks or 0) if use_defaults else 0)
                if max_stacks is not None:
                    stack_count = min(stack_count, max_stacks)
                if stack_count:
                    stacked_value = self._scale(value, multiplier)
                    self._merge(resolved, stat, stacked_value if isinstance(stacked_value, bool) else stacked_value * stack_count)

            upgrade.context["rank"] = rank
            upgrade.stats = resolved
            upgrade.rank_locked_stats = upgrade.conditional_stats = upgrade.stacking_stats = {}
            resolved_upgrades.append(upgrade)

        return Build(*resolved_upgrades)
