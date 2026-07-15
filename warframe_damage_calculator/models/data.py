from __future__ import annotations

from collections.abc import Iterator, Mapping
from copy import deepcopy
from typing import Any, Self


class Data(Mapping[str, Any]):
    """A mutable, attribute-accessible view of nested input data."""

    __slots__ = ("_values",)

    def __init__(self, data: Mapping[str, Any] | None = None, /, **values: Any) -> None:
        source = dict(data or {})
        source.update(values)
        object.__setattr__(self, "_values", {key: self._convert(value) for key, value in source.items()})

    @classmethod
    def _convert(cls, value: Any) -> Any:
        if isinstance(value, Data):
            return value.copy()
        if isinstance(value, Mapping):
            return cls(value)
        if isinstance(value, list):
            return [cls._convert(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls._convert(item) for item in value)
        return value

    def __getattr__(self, name: str) -> Any:
        return self._values.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._values[name] = self._convert(value)

    def __delattr__(self, name: str) -> None:
        try:
            del self._values[name]
        except KeyError:
            raise AttributeError(name) from None

    def __getitem__(self, name: str) -> Any:
        return self._values[name]

    def __setitem__(self, name: str, value: Any) -> None:
        self._values[name] = self._convert(value)

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return f"Data({self.to_dict()!r})"

    @property
    def dict(self) -> dict[str, Any]:
        """Compatibility view for the old Record API."""
        return self._values

    def get(self, name: str, default: Any = None) -> Any:
        return self._values.get(name, default)

    def update(self, values: Mapping[str, Any] | None = None, /, **fields: Any) -> None:
        combined = dict(values or {})
        combined.update(fields)
        for name, value in combined.items():
            self._values[name] = self._convert(value)

    def __or__(self, other: Mapping[str, Any]) -> Self:
        if not isinstance(other, Mapping):
            return NotImplemented
        return type(self)(self.to_dict() | Data(other).to_dict())

    def __ror__(self, other: Mapping[str, Any]) -> Self:
        if not isinstance(other, Mapping):
            return NotImplemented
        return type(self)(Data(other).to_dict() | self.to_dict())

    def __ior__(self, other: Mapping[str, Any]) -> Self:
        self.update(other)
        return self

    def __copy__(self) -> Self:
        return type(self)(self.to_dict())

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        copied = type(self)(deepcopy(self.to_dict(), memo))
        memo[id(self)] = copied
        return copied

    def copy(self) -> Self:
        return type(self)(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        def plain(value: Any) -> Any:
            if isinstance(value, Data):
                return value.to_dict()
            if isinstance(value, list):
                return [plain(item) for item in value]
            if isinstance(value, tuple):
                return tuple(plain(item) for item in value)
            return value

        return {name: plain(value) for name, value in self._values.items()}
