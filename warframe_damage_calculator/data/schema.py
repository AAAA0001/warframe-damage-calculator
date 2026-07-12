from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, TypeAlias, TypedDict


WeaponCategory: TypeAlias = Literal["primary", "secondary", "melee"]
UpgradeCategory: TypeAlias = Literal["mod", "arcane"]
ItemCategory: TypeAlias = WeaponCategory | UpgradeCategory


class WeaponRecord(TypedDict, total=False):
    type: str
    damage: dict[str, float]
    forced_procs: dict[str, float]
    crit_chance: float
    crit_damage: float
    status_chance: float
    trigger: str
    is_beam: bool
    is_battery: bool
    explosion_damage: dict[str, float]
    explosion_forced_procs: dict[str, float]
    multishot: float
    fire_rate: float
    burst_count: int
    burst_delay: float
    charge_time: float
    reload_speed: float
    recharge_rate: float
    magazine_capacity: int
    weakpoint_damage: float
    attack_speed: float


class UpgradeRecord(TypedDict, total=False):
    compatibility: list[str]
    incompatibility: list[str]
    requirements: dict[str, Any]
    max_rank: int
    max_stacks: int
    is_exilus: bool
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
