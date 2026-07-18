from collections.abc import Mapping

from ..calculators.upgrade_calculator import UpgradeCalculator
from ..utils.types import JsonValue
from .data import Data


class Upgrade:
    def __init__(self, data: Mapping[str, JsonValue] | None = None) -> None:
        self.data = Data({"stats": {}, "context": {}} | dict(data or {}))
        self.stats = UpgradeCalculator(self)
