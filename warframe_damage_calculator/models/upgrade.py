from copy import deepcopy

from ..utils.types import JsonValue
from .data import Data
from ..calculators.upgrade_calculator import UpgradeCalculator


class Upgrade:
    def __init__(self, data: dict[str, JsonValue] | None = None) -> None:
        self.data = Data({"stats": {}, "context": {}} | (data or {}))

    def copy(self) -> Upgrade:
        return Upgrade(deepcopy(self.data))

    def resolve(self, build: Data | None = None, weapon: Data | None = None) -> Upgrade:
        return Upgrade(UpgradeCalculator(upgrade=self.data, build=build, weapon=weapon).resolve())
