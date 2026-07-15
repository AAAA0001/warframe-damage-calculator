from collections.abc import Mapping
from typing import Any, Self

from .dist import Dist


DISTRIBUTIONS = {"damage", "forced_procs", "explosion_damage", "explosion_forced_procs"}


class Data(dict[str, Any]):
    def __init__(self, data: Mapping[str, Any] | None = None):
        super().__init__()
        self.update(data or {})

    @classmethod
    def _convert(cls, key, value):
        if key in DISTRIBUTIONS:
            if isinstance(value, list):
                return [cls._distribution(item) for item in value]
            return cls._distribution(value)
        if isinstance(value, Mapping) and not isinstance(value, (Data, Dist)):
            return cls(value)
        if isinstance(value, (list, tuple)):
            return type(value)(cls._convert("", item) for item in value)
        return value.copy() if isinstance(value, Data) else value

    @classmethod
    def _distribution(cls, value):
        if isinstance(value, Dist) or not isinstance(value, Mapping):
            return value
        if "value" not in value:
            return Dist(value)
        effect = cls(value)
        if isinstance(effect.value, Mapping):
            effect.value = Dist(effect.value)
        return effect

    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try: del self[key]
        except KeyError: raise AttributeError(key) from None

    def __setitem__(self, key, value):
        super().__setitem__(key, self._convert(key, value))

    def update(self, data=(), /, **values):
        values = dict(data, **values)
        for key, value in values.items(): self[key] = value

    def copy(self) -> Self:
        return type(self)(self)

    def __or__(self, other) -> Self:
        return type(self)(dict(self) | dict(other))

    def __ror__(self, other) -> Self:
        return type(self)(dict(other) | dict(self))
