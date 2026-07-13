from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, TypeAlias, TypedDict


WeaponCategory: TypeAlias = Literal["primary", "secondary", "melee"]
UpgradeCategory: TypeAlias = Literal["mod", "arcane"]
ItemCategory: TypeAlias = WeaponCategory | UpgradeCategory


class WeaponContext(TypedDict, total=False):
    name: str
    category: WeaponCategory
    type: str
    trigger: str
    is_beam: bool
    is_battery: bool


class UpgradeContext(TypedDict):
    name: str
    category: UpgradeCategory
    compatibility: list[str]
    incompatibility: list[str]
    requirements: dict[str, Any]
    max_rank: int | None
    max_stacks: int | None
    is_exilus: bool


class WeaponRecord(TypedDict):
    context: WeaponContext
    stats: dict[str, Any]


class UpgradeRecord(TypedDict):
    context: UpgradeContext
    stats: dict[str, float | int | bool]
    rank_locked_stats: dict[str, list[Any]]
    conditional_stats: dict[str, list[Any]]
    stacking_stats: dict[str, list[Any]]


DatabaseRecords: TypeAlias = dict[str, dict[str, dict[str, Any]]]


@dataclass(frozen=True, slots=True)
class DatabaseEntry:
    category: ItemCategory
    name: str
    data: Mapping[str, Any]

    @property
    def is_weapon(self) -> bool:
        return self.category in {"primary", "secondary", "melee"}

    @property
    def is_upgrade(self) -> bool:
        return self.category in {"mod", "arcane"}
