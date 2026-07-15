from collections.abc import Mapping
from typing import Any

from .data import Data


class Upgrade:
    def __init__(self, data: Mapping[str, Any] | None = None):
        self.data = Data({"stats": {}, "context": {}} | dict(data or {}))

    def __getattr__(self, key): return getattr(self.data, key)

    def copy(self):
        return Upgrade(self.data)

    def resolve(self):
        from ..calculators.upgrade_calculator import UpgradeCalculator
        return Upgrade(UpgradeCalculator(self).resolve())
