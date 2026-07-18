from collections.abc import Mapping
from typing import Any


class DatabaseEntry:
    def __init__(self, category: str, name: str, data: Mapping[str, Any]) -> None:
        self.category = category
        self.name = name
        self.stats = dict(data.get("stats", {}))
        self.context = dict(data.get("context", data))

    @property
    def is_weapon(self) -> bool:
        return self.category in {"primary", "secondary", "melee"}
