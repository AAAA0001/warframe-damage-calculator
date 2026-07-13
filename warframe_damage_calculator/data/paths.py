import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent
DATABASE_DIR = DATA_DIR / "database"
DEFAULT_WEAPONS_PATH = DATABASE_DIR / "weapons.json"
DEFAULT_UPGRADES_PATH = DATABASE_DIR / "upgrades.json"


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)
