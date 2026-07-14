from __future__ import annotations

from collections.abc import Iterator, Mapping, MutableMapping
from copy import deepcopy
from dataclasses import MISSING, dataclass, field as dataclass_field, fields
from functools import cache
from typing import ClassVar, Generic, Self, TypeVar

from .dist import dist


StatT = TypeVar("StatT")
UpgradeStatT = TypeVar("UpgradeStatT")

DamageInput = dist | Mapping[str, float]
UpgradeValue = float | bool | dist | Mapping[str, float]
ConditionalUpgradeValue = tuple[UpgradeValue, str]
StackingUpgradeValue = tuple[UpgradeValue, str]
RankLockedUpgradeValue = tuple[UpgradeValue, int]


@dataclass(slots=True, kw_only=True)
class Stats(MutableMapping[str, StatT], Generic[StatT]):
    """Typed attribute container with a mutable mapping interface.

    Subclasses declare their supported stats as dataclass fields. Values can be
    read with either attribute syntax (``stats.fire_rate``) or mapping syntax
    (``stats["fire_rate"]``). Fields whose value is ``None`` are treated as
    absent, which lets :class:`UpgradeStats` represent sparse stat buckets.
    """

    _DIST_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        for name in self._DIST_FIELDS:
            if name not in self._field_name_set():
                continue
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, self._coerce_distribution(value))

    @classmethod
    def from_mapping(cls, value: Self | Mapping[str, object] | None = None) -> Self:
        values = {} if value is None else dict(value)
        definitions = {field.name: field for field in fields(cls)}
        unknown = values.keys() - definitions.keys()
        if unknown:
            names = ", ".join(repr(name) for name in sorted(unknown))
            raise TypeError(f"{cls.__name__} received unknown stat(s): {names}")

        instance = cls(**{name: raw for name, raw in values.items() if definitions[name].init})
        for name, raw in values.items():
            if not definitions[name].init:
                instance[name] = raw
        return instance

    @classmethod
    @cache
    def _field_names(cls) -> tuple[str, ...]:
        return tuple(field.name for field in fields(cls))

    @classmethod
    @cache
    def _field_name_set(cls) -> frozenset[str]:
        return frozenset(cls._field_names())

    @staticmethod
    def _coerce_distribution(value: object) -> object:
        if isinstance(value, dist):
            return value
        if isinstance(value, Mapping):
            return dist(value)
        if isinstance(value, (tuple, list)) and len(value) == 2:
            raw_value, qualifier = value
            if isinstance(raw_value, Mapping) and not isinstance(raw_value, dist):
                raw_value = dist(raw_value)
            return raw_value, qualifier
        return value

    @classmethod
    def _default_for(cls, name: str) -> object:
        field = next(field for field in fields(cls) if field.name == name)
        if field.default is not MISSING:
            return deepcopy(field.default)
        if field.default_factory is not MISSING:
            return field.default_factory()
        raise KeyError(name)

    def __getitem__(self, name: str) -> StatT:
        if name not in self._field_name_set():
            raise KeyError(name)
        value = getattr(self, name)
        if value is None:
            raise KeyError(name)
        return value

    def __iter__(self) -> Iterator[str]:
        return (name for name in self._field_names() if getattr(self, name) is not None)

    def __len__(self) -> int:
        return sum(getattr(self, name) is not None for name in self._field_names())

    def __setitem__(self, name: str, value: StatT) -> None:
        if name not in self._field_name_set():
            raise KeyError(f"Unknown stat: {name!r}")
        if name in self._DIST_FIELDS:
            value = self._coerce_distribution(value)  # type: ignore[assignment]
        object.__setattr__(self, name, value)

    def __delitem__(self, name: str) -> None:
        if name not in self._field_name_set():
            raise KeyError(name)
        object.__setattr__(self, name, self._default_for(name))

    def copy(self) -> Self:
        return type(self).from_mapping(deepcopy(dict(self)))

    def to_dict(self) -> dict[str, StatT]:
        return dict(self)


@dataclass(slots=True, kw_only=True)
class WeaponStats(Stats[object]):
    _DIST_FIELDS: ClassVar[frozenset[str]] = frozenset({"damage", "forced_procs"})

    damage: DamageInput = dataclass_field(default_factory=dist)
    forced_procs: DamageInput = dataclass_field(default_factory=dist)
    crit_chance: float = 0.0
    crit_damage: float = 1.0
    status_chance: float = 0.0

    total_damage: float = dataclass_field(default=0.0, init=False)
    multiplicative_base_damage: float = dataclass_field(default=1.0, init=False)
    base_damage: float = dataclass_field(default=0.0, init=False)
    faction_damage: float = dataclass_field(default=1.0, init=False)
    flat_crit_chance: float = dataclass_field(default=0.0, init=False)
    multiplicative_crit_chance: float = dataclass_field(default=1.0, init=False)
    flat_crit_damage: float = dataclass_field(default=0.0, init=False)
    status_damage: float = dataclass_field(default=1.0, init=False)


@dataclass(slots=True, kw_only=True)
class RangedStats(WeaponStats):
    _DIST_FIELDS: ClassVar[frozenset[str]] = WeaponStats._DIST_FIELDS | frozenset(
        {"explosion_damage", "explosion_forced_procs"}
    )

    explosion_damage: DamageInput = dataclass_field(default_factory=dist)
    explosion_forced_procs: DamageInput = dataclass_field(default_factory=dist)
    multishot: float = 1.0
    fire_rate: float = 0.05
    burst_count: int = 1
    burst_delay: float = 0.0
    charge_time: float = 0.0
    reload_speed: float = 0.0
    recharge_rate: float = 0.0
    magazine_capacity: int = 1
    weakpoint_damage: float = 3.0

    explosion_total_damage: float = dataclass_field(default=0.0, init=False)
    multiplicative_fire_rate: float = dataclass_field(default=1.0, init=False)
    ammo_efficiency: float = dataclass_field(default=0.0, init=False)
    multiplicative_weakpoint_crit_chance: float = dataclass_field(default=1.0, init=False)
    weakpoint_crit_chance: float = dataclass_field(default=0.0, init=False)
    internal_bleeding: float = dataclass_field(default=0.0, init=False)


@dataclass(slots=True, kw_only=True)
class MeleeStats(WeaponStats):
    attack_speed: float = 1.0
    melee_doughty: float = dataclass_field(default=0.0, init=False)
    melee_duplicate: float = dataclass_field(default=0.0, init=False)


@dataclass(slots=True, kw_only=True)
class PrimaryStats(RangedStats):
    hunter_munitions: float = dataclass_field(default=0.0, init=False)
    primed_chamber: float = dataclass_field(default=0.0, init=False)
    vigilante_bonus: float = dataclass_field(default=0.0, init=False)


@dataclass(slots=True, kw_only=True)
class SecondaryStats(RangedStats):
    secondary_enervate: float = dataclass_field(default=0.0, init=False)
    secondary_encumber: float = dataclass_field(default=0.0, init=False)


@dataclass(slots=True, kw_only=True)
class UpgradeStats(Stats[UpgradeStatT], Generic[UpgradeStatT]):
    """Sparse typed stats container used by every upgrade bucket.

    The same class is used with different value types:

    - ``UpgradeStats[UpgradeValue]`` for normal stats.
    - ``UpgradeStats[ConditionalUpgradeValue]`` for conditional stats.
    - ``UpgradeStats[StackingUpgradeValue]`` for stacking stats.
    - ``UpgradeStats[RankLockedUpgradeValue]`` for rank-locked stats.
    """

    _DIST_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"damage", "forced_procs", "explosion_damage", "explosion_forced_procs"}
    )

    damage: UpgradeStatT | None = None
    forced_procs: UpgradeStatT | None = None
    explosion_damage: UpgradeStatT | None = None
    explosion_forced_procs: UpgradeStatT | None = None

    impact: UpgradeStatT | None = None
    puncture: UpgradeStatT | None = None
    slash: UpgradeStatT | None = None
    blast: UpgradeStatT | None = None
    corrosive: UpgradeStatT | None = None
    gas: UpgradeStatT | None = None
    magnetic: UpgradeStatT | None = None
    radiation: UpgradeStatT | None = None
    viral: UpgradeStatT | None = None
    cold: UpgradeStatT | None = None
    electricity: UpgradeStatT | None = None
    heat: UpgradeStatT | None = None
    toxin: UpgradeStatT | None = None
    void: UpgradeStatT | None = None

    base_damage: UpgradeStatT | None = None
    multiplicative_base_damage: UpgradeStatT | None = None
    faction_damage: UpgradeStatT | None = None
    weakpoint_damage: UpgradeStatT | None = None
    multishot: UpgradeStatT | None = None

    attack_speed: UpgradeStatT | None = None
    fire_rate: UpgradeStatT | None = None
    multiplicative_fire_rate: UpgradeStatT | None = None
    reload_speed: UpgradeStatT | None = None
    ammo_efficiency: UpgradeStatT | None = None
    magazine_capacity: UpgradeStatT | None = None
    fire_rate_lock: UpgradeStatT | None = None
    multishot_lock: UpgradeStatT | None = None

    crit_chance: UpgradeStatT | None = None
    flat_crit_chance: UpgradeStatT | None = None
    multiplicative_crit_chance: UpgradeStatT | None = None
    weakpoint_crit_chance: UpgradeStatT | None = None
    multiplicative_weakpoint_crit_chance: UpgradeStatT | None = None
    crit_damage: UpgradeStatT | None = None
    flat_crit_damage: UpgradeStatT | None = None

    status_chance: UpgradeStatT | None = None
    status_damage: UpgradeStatT | None = None

    hunter_munitions: UpgradeStatT | None = None
    internal_bleeding: UpgradeStatT | None = None
    primed_chamber: UpgradeStatT | None = None
    vigilante_bonus: UpgradeStatT | None = None
    secondary_enervate: UpgradeStatT | None = None
    secondary_encumber: UpgradeStatT | None = None
    melee_duplicate: UpgradeStatT | None = None
    melee_doughty: UpgradeStatT | None = None

    def __post_init__(self) -> None:
        Stats.__post_init__(self)
        for name in self:
            value = getattr(self, name)
            if isinstance(value, list) and len(value) == 2:
                object.__setattr__(self, name, tuple(value))

