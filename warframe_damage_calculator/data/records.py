from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MatchResult:
    section: str
    name: str
    data: Any
