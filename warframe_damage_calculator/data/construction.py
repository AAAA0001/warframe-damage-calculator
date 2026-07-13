from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from ..models import Melee, Primary, Secondary, Upgrade
from ..utils import Value
from .schema import DatabaseEntry, WeaponCategory


Weapon = Primary | Secondary | Melee
ArsenalItem = Weapon | Upgrade


class DatabaseFactory:
    _weapon_metadata = {"type", "trigger", "is_beam", "is_battery"}
    _weapon_models: dict[WeaponCategory, type[Weapon]] = {
        "primary": Primary,
        "secondary": Secondary,
        "melee": Melee,
    }
    def create(self, entry: DatabaseEntry) -> ArsenalItem:
        if entry.is_weapon:
            return self.create_weapon(entry)
        return self.create_upgrade(entry)

    def create_weapon(self, entry: DatabaseEntry) -> Weapon:
        category = entry.category
        if category not in self._weapon_models:
            raise ValueError(f"Unknown weapon category: {category!r}")

        model = self._weapon_models[category]
        if "context" in entry.data:
            return model(**deepcopy(entry.data))

        context = {"name": entry.name, "category": category, **{key: deepcopy(value) for key, value in entry.data.items() if key in self._weapon_metadata}}
        stats = {key: deepcopy(value) for key, value in entry.data.items() if key not in self._weapon_metadata}

        try:
            return model(stats=stats, context=context)
        except TypeError as exc:
            raise TypeError(
                f"Could not construct {model.__name__} for {entry.name!r}. "
                "Check that the database fields match its public constructor."
            ) from exc

    def create_upgrade(self, entry: DatabaseEntry) -> Upgrade:
        category = entry.category
        if category not in {"mod", "arcane"}:
            raise ValueError(f"Unknown upgrade category: {category!r}")

        if "context" in entry.data:
            return Upgrade(**deepcopy(entry.data))

        max_rank = self._max_rank(entry.data)
        payload = {
            "context": {"name": entry.name, "category": category, "compatibility": set(entry.data.get("compatibility") or ()), "incompatibility": set(entry.data.get("incompatibility") or ()), "requirements": deepcopy(entry.data.get("requirements") or {}), "max_rank": max_rank, "max_stacks": entry.data.get("max_stacks"), "is_exilus": bool(entry.data.get("is_exilus", False))},
            "stats": self._stats(entry.data.get("stats")),
            "rank_locked_stats": self._rank_locked_stats(entry.data.get("rank_locked_stats"), max_rank),
            "conditional_stats": self._conditioned_stats(entry.data.get("conditional_stats")),
            "stacking_stats": self._conditioned_stats(entry.data.get("stacking_stats")),
        }
        return Upgrade(**payload)

    @staticmethod
    def _max_rank(data: Mapping[str, Any]) -> int | None:
        max_rank = data.get("max_rank")
        if max_rank is not None:
            if isinstance(max_rank, bool) or not isinstance(max_rank, int):
                raise TypeError("max_rank in the upgrade database must be an integer")
            if max_rank < 0:
                raise ValueError("max_rank in the upgrade database cannot be negative")

        return max_rank

    @classmethod
    def _rank_locked_stats(
        cls,
        values: Mapping[str, Any] | None,
        max_rank: int | None,
    ) -> dict[str, list[Value | int]]:
        if values and max_rank is None:
            raise ValueError("rank_locked_stats require max_rank in the upgrade database")

        result: dict[str, list[Value | int]] = {}
        for stat, raw_pair in (values or {}).items():
            if not isinstance(raw_pair, (list, tuple)) or len(raw_pair) != 2:
                raise ValueError(
                    f"Database stat {stat!r} must be stored as [value, required_rank]"
                )
            value, required_rank = raw_pair
            if isinstance(required_rank, bool) or not isinstance(required_rank, int):
                raise TypeError(
                    f"Required rank for database stat {stat!r} must be an integer"
                )
            if required_rank < 0:
                raise ValueError(
                    f"Required rank for database stat {stat!r} cannot be negative"
                )
            result[stat] = [cls._validate_value(value), required_rank]
        return result

    @classmethod
    def _stats(cls, values: Mapping[str, Value] | None) -> dict[str, Value]:
        return {stat: cls._validate_value(value) for stat, value in (values or {}).items()}

    @classmethod
    def _conditioned_stats(cls, values: Mapping[str, Any] | None) -> dict[str, list[Value | str]]:
        result: dict[str, list[Value | str]] = {}
        for stat, raw_pair in (values or {}).items():
            if not isinstance(raw_pair, (list, tuple)) or len(raw_pair) != 2:
                raise ValueError(
                    f"Database stat {stat!r} must be stored as [value, condition]"
                )
            value, condition = raw_pair
            if not isinstance(condition, str) or not condition.strip():
                raise ValueError(f"Database stat {stat!r} has an invalid condition")
            result[stat] = [cls._validate_value(value), condition]
        return result

    @staticmethod
    def _validate_value(value: Value) -> Value:
        if not isinstance(value, (bool, int, float)):
            raise TypeError(f"Upgrade stat values must be numeric or bool, got {value!r}")
        return value
