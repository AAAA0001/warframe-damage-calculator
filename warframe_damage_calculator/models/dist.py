from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping

from ..utils import DAMAGE_TYPE_ORDER, DAMAGE_TYPES, ELEMENTAL_COMBINATIONS, ELEMENTAL_TYPES, PHYSICAL_TYPES, DamageType


class dist:
    __slots__ = ("_values",)

    def __init__(self, values: Mapping[DamageType, float] | None = None, /, **kwargs: float) -> None:
        merged = dict(values or {})
        merged.update(kwargs)
        unknown = set(merged) - set(DAMAGE_TYPES)
        if unknown:
            raise ValueError(f"Unknown damage types: {', '.join(sorted(unknown))}")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in merged.values()):
            raise TypeError("Damage values must be numeric")
        self._values = {damage_type: float(value) for damage_type, value in merged.items() if value != 0}

    def __iter__(self) -> Iterator[tuple[DamageType, float]]:
        return iter(self._values.items())

    def __repr__(self) -> str:
        return f"dist({self._values!r})"

    def __str__(self) -> str:
        return ", ".join(f"{damage_type}: {value}" for damage_type, value in self)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, dist) and self._values == other._values

    def __add__(self, other: dist) -> dist:
        if not isinstance(other, dist):
            return NotImplemented
        return dist({damage_type: self.get(damage_type) + other.get(damage_type) for damage_type in self._values | other._values})

    def __radd__(self, other: int) -> dist:
        return self if other == 0 else NotImplemented

    def __mul__(self, multiplier: int | float) -> dist:
        if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)):
            return NotImplemented
        return dist({damage_type: value * multiplier for damage_type, value in self})

    __rmul__ = __mul__

    def get(self, damage_type: DamageType) -> float:
        return self._values.get(damage_type, 0.0)

    def total_damage(self) -> float:
        return sum(self._values.values())

    def weight(self, damage_type: DamageType) -> float:
        total = self.total_damage()
        return self.get(damage_type) / total if total else 0.0

    def include(self, damage_types: Iterable[DamageType]) -> dist:
        included = set(damage_types)
        return dist({damage_type: value for damage_type, value in self if damage_type in included})

    def exclude(self, damage_types: Iterable[DamageType]) -> dist:
        excluded = set(damage_types)
        return dist({damage_type: value for damage_type, value in self if damage_type not in excluded})

    def positive(self) -> dist:
        return dist({damage_type: value for damage_type, value in self if value > 0})

    def apply(self, upgrades: dist) -> dist:
        total = self.total_damage()
        return dist({damage_type: self.get(damage_type) * (1 + upgrades.get(damage_type)) if damage_type in PHYSICAL_TYPES else self.get(damage_type) + total * upgrades.get(damage_type) for damage_type in self._values | upgrades._values})

    def combine(self) -> dist:
        elements = list(self.include(ELEMENTAL_TYPES))
        combined: dict[DamageType, float] = {}
        pairs = zip(elements[::2], elements[1::2] + [(None, 0.0)])
        for (first_type, first_value), (second_type, second_value) in pairs:
            result_type = ELEMENTAL_COMBINATIONS.get(frozenset((first_type, second_type)), first_type)
            combined[result_type] = first_value + second_value
        return (self.exclude(ELEMENTAL_TYPES) + dist(combined)).positive()

    def sorted(self) -> dist:
        ordered = sorted(self._values.items(), key=lambda item: DAMAGE_TYPE_ORDER[item[0]])
        return dist(dict(ordered))
