from collections.abc import Mapping
from copy import deepcopy
from typing import Self

from ..utils.types import DataValue


class Data(dict[str, DataValue]):
    def __init__(self, data: Mapping[str, DataValue] | None = None) -> None:
        super().__init__()
        self.update(data or {})

    @classmethod
    def _convert(cls, value: DataValue) -> DataValue:
        if isinstance(value, Data): return value
        if isinstance(value, Mapping): return cls(value)
        if isinstance(value, list): return [cls._convert(item) for item in value]
        return value

    def __getattr__(self, key: str) -> DataValue:
        try: return self[key]
        except KeyError: raise AttributeError(key) from None

    def __delattr__(self, key: str) -> None:
        try: del self[key]
        except KeyError: raise AttributeError(key) from None

    def __setattr__(self, key: str, value: DataValue) -> None:
        dict.__setitem__(self, key, self._convert(value))

    __setitem__ = __setattr__

    def __or__(self, other: Mapping[str, DataValue]) -> Self:
        return Data(dict(self) | dict(other))

    def __ror__(self, other: Mapping[str, DataValue]) -> Self:
        return Data(dict(other) | dict(self))

    def update(self, data: Mapping[str, DataValue], /) -> None:
        for key, value in data.items(): self[key] = value

    def copy(self) -> Self:
        return deepcopy(self)
