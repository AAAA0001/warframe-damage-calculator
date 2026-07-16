from typing import Any, Self

from .dist import Dist


DISTRIBUTIONS = {"damage", "forced_procs", "explosion_damage", "explosion_forced_procs"}


class Data(dict[str, Any]):
    def __init__(self, data: dict[str, Any] | None = None) -> None:
        super().__init__()
        self.update(data or {})

    @classmethod
    def _convert(cls, key: str, value: Any) -> Any:
        if isinstance(value, dict):
            return cls._distribution(value) if key in DISTRIBUTIONS else cls(value)
        if isinstance(value, list):
            return [cls._convert(key, item) for item in value]
        return value

    @classmethod
    def _distribution(cls, value: Any) -> Any:
        if "value" not in value: return Dist(value)
        return cls(value | {"value": Dist(value["value"])})

    def __getattr__(self, key: str) -> Any:
        try: return self[key]
        except KeyError: raise AttributeError(key) from None

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def __delattr__(self, key: str) -> None:
        try: del self[key]
        except KeyError: raise AttributeError(key) from None

    def __setitem__(self, key: str, value: Any) -> None:
        dict.__setitem__(self, key, self._convert(key, value))

    def update(self, data: dict[str, Any] | None = None) -> None:
        for key, value in {**(data or {})}.items():
            self[key] = value

    def copy(self) -> Data:
        return Data(self)

    def __or__(self, other: dict[str, Any] | Data) -> Data:
        return Data(dict(self) | dict(other))

    def __ror__(self, other: dict[str, Any]) -> Data:
        return Data(other | dict(self))
