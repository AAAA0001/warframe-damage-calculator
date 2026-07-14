from ..utils import DAMAGE_TYPE_ORDER, ELEMENTAL_COMBINATIONS, ELEMENTAL_TYPES, PHYSICAL_TYPES


class Dist:
    __slots__ = ("_values",)

    def __init__(self, values=None):
        self._values = {damage_type: float(value) for damage_type, value in (values or {}).items() if value}

    def __iter__(self):
        return iter(self._values.items())

    def __repr__(self):
        return f"dist({self._values!r})"

    def __str__(self):
        return ", ".join(f"{damage_type}: {value}" for damage_type, value in self)

    def __eq__(self, other):
        return isinstance(other, Dist) and self._values == other._values

    def __add__(self, other):
        if not isinstance(other, Dist):
            return NotImplemented
        return Dist({damage_type: self.get(damage_type) + other.get(damage_type) for damage_type in self._values | other._values})

    def __radd__(self, other):
        return self if other == 0 else NotImplemented

    def __mul__(self, multiplier):
        return Dist({damage_type: value * multiplier for damage_type, value in self})

    __rmul__ = __mul__

    def get(self, damage_type):
        return self._values.get(damage_type, 0.0)

    def total_damage(self):
        return sum(self._values.values())

    def weight(self, damage_type):
        total = self.total_damage()
        return self.get(damage_type) / total if total else 0.0

    def include(self, damage_types):
        included = set(damage_types)
        return Dist({damage_type: value for damage_type, value in self if damage_type in included})

    def exclude(self, damage_types):
        excluded = set(damage_types)
        return Dist({damage_type: value for damage_type, value in self if damage_type not in excluded})

    def positive(self):
        return Dist({damage_type: value for damage_type, value in self if value > 0})

    def apply(self, upgrades):
        total = self.total_damage()
        return Dist({damage_type: self.get(damage_type) * (1 + upgrades.get(damage_type)) if damage_type in PHYSICAL_TYPES else self.get(damage_type) + total * upgrades.get(damage_type) for damage_type in self._values | upgrades._values})

    def combine(self):
        elements = list(self.include(ELEMENTAL_TYPES))
        combined = {}
        pairs = zip(elements[::2], elements[1::2] + [(None, 0.0)])
        for (first_type, first_value), (second_type, second_value) in pairs:
            result_type = ELEMENTAL_COMBINATIONS.get(frozenset((first_type, second_type)), first_type)
            combined[result_type] = first_value + second_value
        return (self.exclude(ELEMENTAL_TYPES) + Dist(combined)).positive()

    def sorted(self):
        ordered = sorted(self._values.items(), key=lambda item: DAMAGE_TYPE_ORDER[item[0]])
        return Dist(dict(ordered))
