from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

from .dist import Dist
from .melee import Melee
from .ranged import Ranged
from .upgrade import Upgrade

DAMAGE_TYPES = {"impact", "puncture", "slash","blast", "corrosive", "gas", "magnetic", "radiation", "viral","cold", "electricity", "heat", "toxin"}
UPGRADE_FIELDS = {field.name for field in fields(Upgrade)} - {"damage_dist"}
WEAPON_TABLES = ("primary", "secondary", "melee")
UPGRADE_TABLES = ("mod", "arcane")

class Database:
    def __init__(self, root: Path|None=None) -> None:
        base_root = root or Path(__file__).resolve().parents[1] / "database"
        filenames = {"primary": "primaries.json", "secondary": "secondaries.json", "melee": "melees.json", "mod": "mods.json", "arcane": "arcanes.json"}
        self.tables = {table: json.loads((base_root / filename).read_text(encoding="utf-8")) for table, filename in filenames.items()}

    @staticmethod
    def rank_value(series: object, rank: int | None) -> float:
        if not series: return 0.0
        if not isinstance(series, list): return float(series)
        if rank is None: rank = len(series) - 1
        return float(series[max(0, min(rank, len(series) - 1))])

    @staticmethod
    def add(mapping: dict[str, float], key: str, value: float) -> None:
        mapping[key] = mapping.get(key, 0.0) + value

    def find(self, tables: tuple[str], name: str) -> tuple[str, dict]:
        for table in tables:
            record = self.tables[table].get(name)
            if record is not None: return table, record
        raise KeyError(f"Unknown object: {name}")

    def weapon(self, name: str) -> Melee | Ranged:
        table, record = self.find(WEAPON_TABLES, name)
        common = {"base_damage_dist": Dist(**record.get("damage_dist", {})), "base_crit_chance": float(record.get("crit_chance", 0.0)), "base_crit_damage": float(record.get("crit_damage", 0.0)), "base_status_chance": float(record.get("status_chance", 0.0))}
        if table == "melee": return Melee(**common, base_attack_speed=float(record.get("attack_speed", record.get("attack_speed", 0.0))))
        return Ranged(**common, base_explosion_damage_dist=Dist(**record.get("explosion_damage_dist", {})), forced_procs=Dist(**record.get("forced_procs", {})), base_fire_rate=float(record.get("fire_rate", 0.0)), base_charge_time=float(record.get("charge_time", 0.0)), base_reload_speed=float(record.get("reload_speed", 0.0)), base_magazine_capacity=int(record.get("magazine_capacity", 0)), base_multishot=float(record.get("multishot", 1.0)), is_beam=bool(record.get("is_beam", False)))

    def upgrade(self, name: str, rank: int|None=None, stacks: int|None=None, conditional: bool|None=None) -> Upgrade:
        _, record = self.find(UPGRADE_TABLES, name)

        stats: dict[str, float] = {}
        damage_stats: dict[str, float] = {}

        max_stacks = int(record.get("max stacks", 1))
        stack_count = max(0, min(max_stacks if stacks is None else stacks, max_stacks))

        for section, multiplier in (("stats", 1), ("conditional stats", conditional is not False), ("stacks", stack_count)):
            raw_stats = record.get(section, {})
            for stat_name, series in raw_stats.items():
                value = float(multiplier) * self.rank_value(series, rank)
                if stat_name in DAMAGE_TYPES: self.add(damage_stats, stat_name, value)
                elif stat_name in UPGRADE_FIELDS: self.add(stats, stat_name, value)

        return Upgrade(damage_dist=Dist(**damage_stats), **stats)

default_database = Database()

def load_weapon(name: str) -> Melee | Ranged:
    return default_database.weapon(name)

def load_upgrade(name: str, rank: int|None=None, stacks: int|None=None, conditional: bool|None=None) -> Upgrade:
    return default_database.upgrade(name, rank, stacks, conditional)