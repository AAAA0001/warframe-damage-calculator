from __future__ import annotations

from pathlib import Path
from typing import Any
import json

DATA_DIR = Path(__file__).resolve().parent
DATABASE_DIR = DATA_DIR / "database"
DEFAULT_WEAPONS_PATH = DATABASE_DIR / "weapons.json"
DEFAULT_UPGRADES_PATH = DATABASE_DIR / "upgrades.json"


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)
