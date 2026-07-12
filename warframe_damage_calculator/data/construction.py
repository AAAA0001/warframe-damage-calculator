from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, get_type_hints

from ..fields import MeleeFields, PrimaryFields, SecondaryFields
from ..models import Melee, Primary, Secondary, Upgrade
from ..utils import Value
from .schema import DatabaseEntry, WeaponCategory


Weapon = Primary | Secondary | Melee
ArsenalItem = Weapon | Upgrade


class DatabaseFactory:
    _weapon_models: dict[WeaponCategory, type[Weapon]] = {
        "primary": Primary,
        "secondary": Secondary,
        "melee": Melee,
    }
    _weapon_fields: dict[WeaponCategory, frozenset[str]] = {
        "primary": frozenset(get_type_hints(PrimaryFields)),
        "secondary": frozenset(get_type_hints(SecondaryFields)),
        "melee": frozenset(get_type_hints(MeleeFields)),
    }

    def create(self, entry: DatabaseEntry, *, rank: int | None = None) -> ArsenalItem:
        if entry.is_weapon:
            return self.create_weapon(entry)
        return self.create_upgrade(entry, rank=rank)

    def create_weapon(self, entry: DatabaseEntry) -> Weapon:
        category = entry.category
        if category not in self._weapon_models:
            raise ValueError(f"Unknown weapon category: {category!r}")

        allowed_fields = self._weapon_fields[category]
        payload = {key: value for key, value in entry.data.items() if key in allowed_fields}
        payload["name"] = entry.name

        model = self._weapon_models[category]
        try:
            return model(**payload)
        except TypeError as exc:
            raise TypeError(
                f"Could not construct {model.__name__} for {entry.name!r}. "
                "Check that the database fields match its public constructor."
            ) from exc

    def create_upgrade(self, entry: DatabaseEntry, *, rank: int | None = None) -> Upgrade:
        category = entry.category
        if category not in {"mod", "arcane"}:
            raise ValueError(f"Unknown upgrade category: {category!r}")

        effective_rank, multiplier = self._rank_values(entry.data, rank)
        payload = {
            "name": entry.name,
            "category": category,
            "compatibility": set(entry.data.get("compatibility") or ()),
            "incompatibility": set(entry.data.get("incompatibility") or ()),
            "requirements": deepcopy(entry.data.get("requirements") or {}),
            "max_rank": entry.data.get("max_rank"),
            "max_stacks": entry.data.get("max_stacks"),
            "is_exilus": bool(entry.data.get("is_exilus", False)),
            "stats": self._resolved_stats(entry.data, effective_rank, multiplier),
            "conditional_stats": self._scaled_conditioned_stats(
                entry.data.get("conditional_stats"), multiplier
            ),
            "stacking_stats": self._scaled_conditioned_stats(
                entry.data.get("stacking_stats"), multiplier
            ),
        }
        return Upgrade(**payload)

    @staticmethod
    def _rank_values(
        data: Mapping[str, Any],
        rank: int | None,
    ) -> tuple[int | None, float]:
        max_rank = data.get("max_rank")
        if max_rank is not None:
            if isinstance(max_rank, bool) or not isinstance(max_rank, int):
                raise TypeError("max_rank in the upgrade database must be an integer")
            if max_rank < 0:
                raise ValueError("max_rank in the upgrade database cannot be negative")

        if rank is not None and (isinstance(rank, bool) or not isinstance(rank, int)):
            raise TypeError("rank must be an integer or None")

        if max_rank is None:
            return rank, 1.0

        effective_rank = max_rank if rank is None else max(0, min(rank, max_rank))
        if max_rank == 0:
            return effective_rank, 1.0
        return effective_rank, (effective_rank + 1) / (max_rank + 1)

    @classmethod
    def _resolved_stats(
        cls,
        data: Mapping[str, Any],
        effective_rank: int | None,
        multiplier: float,
    ) -> dict[str, Value]:
        result = cls._scaled_stats(data.get("stats"), multiplier)
        unlocked = cls._unlocked_rank_stats(
            data.get("rank_locked_stats"),
            effective_rank,
        )
        cls._merge_stats(result, unlocked)
        return result

    @classmethod
    def _unlocked_rank_stats(
        cls,
        values: Mapping[str, Any] | None,
        effective_rank: int | None,
    ) -> dict[str, Value]:
        if values and effective_rank is None:
            raise ValueError("rank_locked_stats require max_rank in the upgrade database")

        result: dict[str, Value] = {}
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
            if effective_rank is not None and effective_rank >= required_rank:
                result[stat] = cls._scale_value(value, 1.0)
        return result

    @staticmethod
    def _merge_stats(target: dict[str, Value], source: Mapping[str, Value]) -> None:
        for stat, value in source.items():
            if stat not in target:
                target[stat] = value
                continue

            current = target[stat]
            if isinstance(current, bool) or isinstance(value, bool):
                if current != value:
                    raise ValueError(
                        f"Conflicting boolean values for upgrade stat {stat!r}"
                    )
                continue

            if not isinstance(current, (int, float)) or not isinstance(value, (int, float)):
                raise TypeError(f"Upgrade stat values must be numeric or bool, got {value!r}")
            target[stat] = current + value

    @classmethod
    def _scaled_stats(
        cls,
        values: Mapping[str, Value] | None,
        multiplier: float,
    ) -> dict[str, Value]:
        return {
            stat: cls._scale_value(value, multiplier)
            for stat, value in (values or {}).items()
        }

    @classmethod
    def _scaled_conditioned_stats(
        cls,
        values: Mapping[str, Any] | None,
        multiplier: float,
    ) -> dict[str, tuple[Value, str]]:
        result: dict[str, tuple[Value, str]] = {}
        for stat, raw_pair in (values or {}).items():
            if not isinstance(raw_pair, (list, tuple)) or len(raw_pair) != 2:
                raise ValueError(
                    f"Database stat {stat!r} must be stored as [value, condition]"
                )
            value, condition = raw_pair
            if not isinstance(condition, str) or not condition.strip():
                raise ValueError(f"Database stat {stat!r} has an invalid condition")
            result[stat] = (cls._scale_value(value, multiplier), condition)
        return result

    @staticmethod
    def _scale_value(value: Value, multiplier: float) -> Value:
        if isinstance(value, bool) or multiplier == 1.0:
            return value
        if not isinstance(value, (int, float)):
            raise TypeError(f"Upgrade stat values must be numeric or bool, got {value!r}")
        return value * multiplier
