from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..utils import DAMAGE_TYPES, Value
from ..models import Build, Upgrade, dist


class UpgradeResolver:
    METADATA = {"name", "category", "type", "trigger", "is beam", "is battery", "compatibility", "incompatibility", "requirements", "max rank", "max stacks", "is exilus"}
    AUTOMATIC_CONDITIONS = {"primary", "rifle", "bow", "shotgun", "sniper", "secondary", "pistol", "melee", "sacrificial set"}

    def __init__(self, weapon_context: Mapping[str, Any]) -> None:
        self.weapon_context = weapon_context

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().replace("_", " ").replace("-", " ").split())

    @property
    def context(self) -> dict[str, Any]:
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

    def _resolve_context(self, upgrade: Upgrade, shared_context: Mapping[str, Any]) -> dict[str, Any]:
        context = {**{self._normalize(key): value for key, value in upgrade.context.items()}, **shared_context}
        context.setdefault("rank", context.get("max rank") or 0)
        return context

    def _condition_active(self, condition: str, context: dict[str, Any], use_defaults: bool) -> bool:
        condition = self._normalize(condition)
        default = False if condition in self.AUTOMATIC_CONDITIONS else use_defaults
        return bool(context.get(condition, default))

    @staticmethod
    def _scale(value: Value, multiplier: float) -> Value:
        return value if isinstance(value, bool) else value * multiplier

    @staticmethod
    def _merge(target: dict[str, Value], stat: str, value: Value) -> None:
        if stat in DAMAGE_TYPES:
            value = dist({stat: value})
            stat = "damage"
        current = target.get(stat)
        if current is None:
            target[stat] = value
        elif isinstance(current, bool) and isinstance(value, bool):
            target[stat] = current or value
        elif isinstance(current, bool) or isinstance(value, bool):
            raise TypeError(f"Cannot merge values for upgrade stat {stat!r}")
        else:
            try:
                target[stat] = current + value
            except TypeError:
                raise TypeError(f"Cannot merge values for upgrade stat {stat!r}") from None

    def resolve(self, build: Build) -> Build:
        names = {self._normalize(str(upgrade.context.get("name") or "")) for upgrade in build}
        shared_context = {**self.context, "sacrificial set": {"sacrificial pressure", "sacrificial steel"}.issubset(names)}
        resolved_upgrades = []

        for source in build:
            upgrade = source.copy()
            upgrade_name = upgrade.context.get("name") or "<unnamed>"
            context = self._resolve_context(upgrade, shared_context)
            use_defaults = not any(key not in self.AUTOMATIC_CONDITIONS | self.METADATA | {"rank", "weapon"} for key in context)
            resolved: dict[str, Value] = {}
            max_rank = context.get("max rank")
            max_stacks = context.get("max stacks")
            rank = context.get("rank", 0)
            if isinstance(rank, bool) or not isinstance(rank, int) or rank < 0:
                raise ValueError(f"Invalid rank {rank!r} for upgrade {upgrade_name!r}; rank must be a non-negative integer")
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
                if isinstance(stack_count, bool) or not isinstance(stack_count, int) or stack_count < 0:
                    raise ValueError(f"Invalid stack count {stack_count!r} for condition {condition!r} on upgrade {upgrade_name!r}; stack count must be a non-negative integer")
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
