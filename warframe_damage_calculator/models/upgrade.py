from ..utils import JsonValue
from ..calculators import UpgradeCalculator
from .data import Data


class Upgrade:
    def __init__(self, data: dict[str, JsonValue] | None = None) -> None:
        self.data = Data({"stats": {}, "context": {}} | (data or {}))

    def copy(self) -> Upgrade:
        return Upgrade(self.data)

    def resolve(self) -> Upgrade:
        return Upgrade(UpgradeCalculator(self.data).resolve())