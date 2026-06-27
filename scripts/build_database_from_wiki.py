import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from slpp import slpp as lua

ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATHS = {
    "primary":   ROOT / "database" / "primaries.json",
    "secondary": ROOT / "database" / "secondaries.json",
    "melee":     ROOT / "database" / "melees.json",
    "mods":      ROOT / "database" / "mods.json",
    "arcanes":   ROOT / "database" / "arcanes.json",
}

WIKI_LUA_CACHE_PATHS = {
    "primary":   ROOT / "database" / "wiki_primary.lua",
    "secondary": ROOT / "database" / "wiki_secondary.lua",
    "melee":     ROOT / "database" / "wiki_melee.lua",
    "mods":      ROOT / "database" / "wiki_mods.lua",
    "arcane":    ROOT / "database" / "wiki_arcane.lua",
}

WIKI_MODULE_TITLES = {
    "primary":   "Module:Weapons/data/primary",
    "secondary": "Module:Weapons/data/secondary",
    "melee":     "Module:Weapons/data/melee",
    "mods":      "Module:Mods/data",
    "arcane":    "Module:Arcane/data",
}

WIKI_API = "https://warframe.fandom.com/api.php"

# ---------------------------------------------------------------------------
# Weapon constants
# ---------------------------------------------------------------------------

DAMAGE_KEYS = {
    "impact", "puncture", "slash",
    "blast", "corrosive", "gas", "magnetic", "radiation", "viral",
    "cold", "electricity", "heat", "toxin",
}

# ---------------------------------------------------------------------------
# Upgrade constants
# ---------------------------------------------------------------------------

ALLOWED_MOD_TYPES = {"rifle", "primary", "pistol", "secondary", "shotgun", "melee"}
ALLOWED_ARCANE_TYPES = {"primary", "secondary"}

STAT_PATTERNS = [
    (r"weak\s*point\s*critical chance|critical chance.*weak\s*point", "weakpoint_crit_chance"),
    (r"weak\s*point\s*damage|damage.*weak\s*point|headshot\s*multiplier",  "weakpoint_damage"),
    (r"critical chance",    "crit_chance"),
    (r"critical damage",    "crit_damage"),
    (r"status chance",      "status_chance"),
    (r"status damage",      "status_damage"),
    (r"reload speed",       "reload_speed"),
    (r"magazine capacity",  "magazine_capacity"),
    (r"multishot",          "multishot"),
    (r"fire rate",          "fire_rate"),
    (r"damage",             "base_damage"),
    (r"impact",             "impact"),
    (r"puncture",           "puncture"),
    (r"slash",              "slash"),
    (r"blast",              "blast"),
    (r"corrosive",          "corrosive"),
    (r"gas",                "gas"),
    (r"magnetic",           "magnetic"),
    (r"radiation",          "radiation"),
    (r"viral",              "viral"),
    (r"cold",               "cold"),
    (r"electricity",        "electricity"),
    (r"heat",               "heat"),
    (r"toxin",              "toxin"),
]

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def fetch_wiki_module(module_name: str) -> dict:
    if module_name not in WIKI_MODULE_TITLES:
        raise ValueError(f"Unknown wiki module: {module_name}")

    query = {
        "action": "query",
        "prop": "revisions",
        "titles": WIKI_MODULE_TITLES[module_name],
        "rvprop": "content",
        "rvslots": "main",
        "formatversion": "2",
        "format": "json",
    }
    url = f"{WIKI_API}?{urlencode(query)}"
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json,text/plain,*/*",
        },
    )

    content = None
    try:
        with urlopen(req) as resp:
            payload = json.load(resp)
        content = payload["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
    except HTTPError:
        cache_path = WIKI_LUA_CACHE_PATHS.get(module_name)
        if cache_path and cache_path.exists():
            content = cache_path.read_text(encoding="utf-8")

    if not content:
        raise RuntimeError(f"Could not retrieve wiki {module_name} module source")

    content = content.replace("math.huge", "1e30")
    content = re.sub(r"(?m)--.*$", "", content)
    content = re.sub(r"^\s*return\s*", "", content, count=1)
    return lua.decode(content)


def normalize_lua_lists(obj):
    if isinstance(obj, dict):
        if obj and all(isinstance(k, int) for k in obj.keys()):
            return [normalize_lua_lists(obj[k]) for k in sorted(obj.keys())]
        return {k: normalize_lua_lists(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_lua_lists(v) for v in obj]
    return obj

# ---------------------------------------------------------------------------
# Weapon helpers
# ---------------------------------------------------------------------------

def to_damage_dist(damage_obj) -> dict:
    if not isinstance(damage_obj, dict):
        return {}
    out = {}
    for k, v in damage_obj.items():
        lk = str(k).strip().lower()
        if lk in DAMAGE_KEYS:
            out[lk] = float(v)
    return out


def forced_proc_dist(attack: dict) -> dict:
    procs = attack.get("ForcedProcs")
    if not procs:
        return {}
    if isinstance(procs, str):
        procs = [procs]
    if not isinstance(procs, list):
        return {}
    out = {}
    for proc in procs:
        key = str(proc).strip().lower()
        if key in DAMAGE_KEYS:
            out[key] = out.get(key, 0.0) + 1.0
    return out


def attack_penalty(attack_name: str) -> int:
    name = attack_name.lower()
    penalty = 0
    if re.search(r"\b(normal\s+attack|primary(\s+fire)?|buckshot|auto)\b", name):
        penalty -= 4
    if re.search(r"\b(alt|alternate|zoom|incarnon|secondary\s+fire|air\s+burst|charged|charge\s+shot|detonation|detonate|grenade|launcher|glaive)\b", name):
        penalty += 8
    if "heavy" in name or "slam" in name or "slide" in name or "aerial" in name:
        penalty += 3
    if "throw" in name:
        penalty += 2
    return penalty


def choose_primary_attack(attacks: list[dict], *, skip_aoe: bool) -> tuple[int, dict] | tuple[None, None]:
    candidates = []
    for i, atk in enumerate(attacks):
        if not isinstance(atk, dict):
            continue
        damage = to_damage_dist(atk.get("Damage"))
        if not damage:
            continue
        shot_type = str(atk.get("ShotType", "")).lower()
        if skip_aoe and shot_type == "aoe":
            continue
        penalty = attack_penalty(str(atk.get("AttackName", "")))
        if skip_aoe and not atk.get("Trigger"):
            penalty += 2
        dmg_total = sum(damage.values())
        candidates.append((penalty, 1 if shot_type == "aoe" else 0, -dmg_total, i, atk))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: x[:3])
    _, _, _, idx, attack = candidates[0]
    return idx, attack


def choose_explosion_attack(primary_idx: int, primary_atk: dict, attacks: list[dict]) -> dict | None:
    if primary_idx is None:
        return None
    pcrit = float(primary_atk.get("CritChance", 0.0))
    pstat = float(primary_atk.get("StatusChance", 0.0))
    pfire = float(primary_atk.get("FireRate", 0.0))
    best = None
    best_score = float("inf")
    for i, atk in enumerate(attacks):
        if not isinstance(atk, dict):
            continue
        if str(atk.get("ShotType", "")).lower() != "aoe":
            continue
        damage = to_damage_dist(atk.get("Damage"))
        if not damage:
            continue
        score = 0.0
        score += abs(float(atk.get("CritChance", pcrit)) - pcrit) * 20
        score += abs(float(atk.get("StatusChance", pstat)) - pstat) * 20
        score += abs(float(atk.get("FireRate", pfire)) - pfire) * 2
        score += abs(i - primary_idx) * 0.5
        name = str(atk.get("AttackName", "")).lower()
        if "alt" in name and "explosion" not in name and "radial" not in name:
            score += 4
        if "incarnon" in name:
            score += 6
        if score < best_score:
            best_score = score
            best = atk
    if best is None or best_score > 8:
        return None
    return best


def parse_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def order_weapon_record(record: dict) -> dict:
    ordered = {}
    key_order = [
        "damage_dist",
        "forced_procs",
        "explosion_damage_dist",
        "explosion_forced_procs",
        "crit_chance",
        "crit_damage",
        "status_chance",
        "fire_rate",
        "charge_time",
        "reload_speed",
        "magazine_capacity",
        "multishot",
        "is_beam",
    ]
    for key in key_order:
        if key in record:
            ordered[key] = record[key]
    for key, value in record.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def build_ranged_record(wiki_weapon: dict) -> dict | None:
    attacks = wiki_weapon.get("Attacks") or []
    if not isinstance(attacks, list):
        return None
    primary_idx, primary_atk = choose_primary_attack(attacks, skip_aoe=True)
    if primary_atk is None:
        return None
    primary_damage = to_damage_dist(primary_atk.get("Damage"))
    if not primary_damage:
        return None
    record = {
        "damage_dist": primary_damage,
        "crit_chance":    parse_float(primary_atk.get("CritChance"), 0.0),
        "crit_damage":    parse_float(primary_atk.get("CritMultiplier"), 0.0),
        "status_chance":  parse_float(primary_atk.get("StatusChance"), 0.0),
        "fire_rate":      parse_float(primary_atk.get("FireRate"), 0.0),
        "reload_speed":   parse_float(wiki_weapon.get("Reload"), 0.0),
        "magazine_capacity": parse_int(wiki_weapon.get("Magazine"), 0),
        "multishot":      parse_float(primary_atk.get("Multishot"), 1.0),
        "is_beam": "BEAM" in (wiki_weapon.get("CompatibilityTags") or []),
    }
    charge_time = primary_atk.get("ChargeTime")
    if charge_time is not None:
        record["charge_time"] = parse_float(charge_time, 0.0)
    explosion = choose_explosion_attack(primary_idx, primary_atk, attacks)
    if explosion is not None:
        explosion_damage = to_damage_dist(explosion.get("Damage"))
        if explosion_damage:
            record["explosion_damage_dist"] = explosion_damage
        explosion_procs = forced_proc_dist(explosion)
        if explosion_procs:
            record["explosion_forced_procs"] = explosion_procs
    procs = forced_proc_dist(primary_atk)
    if procs:
        record["forced_procs"] = procs
    return order_weapon_record(record)


def build_melee_record(wiki_weapon: dict) -> dict | None:
    attacks = wiki_weapon.get("Attacks") or []
    if not isinstance(attacks, list):
        return None
    _, primary_atk = choose_primary_attack(attacks, skip_aoe=False)
    if primary_atk is None:
        return None
    primary_damage = to_damage_dist(primary_atk.get("Damage"))
    if not primary_damage:
        return None
    record = {
        "damage_dist":   primary_damage,
        "crit_chance":   parse_float(primary_atk.get("CritChance"), 0.0),
        "crit_damage":   parse_float(primary_atk.get("CritMultiplier"), 0.0),
        "status_chance": parse_float(primary_atk.get("StatusChance"), 0.0),
        "attack_speed":       parse_float(primary_atk.get("FireRate"), 0.0),
    }
    return order_weapon_record(record)

# ---------------------------------------------------------------------------
# Upgrade helpers
# ---------------------------------------------------------------------------


def to_lines(desc: str) -> list[str]:
    text = str(desc or "")
    text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    text = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


def find_stat_key(text: str, *, mod_name: str = "") -> str | None:
    low = text.lower()
    mod_low = mod_name.lower()
    if re.search(r"\bdamage\s+(to|against)\b", low):
        return "faction_damage"
    if mod_low == "hunter munitions" and "critical" in low and "chance to apply" in low:
        return "hunter_munitions"
    if "chance to apply" in low and "slash status" in low:
        if "critical" in low:
            return "hunter_munitions"
        return "internal_bleeding"
    if "vigilante" in mod_name.lower() and "set" in low and "%" in low:
        return "vigilante_bonus"
    for pattern, stat in STAT_PATTERNS:
        if re.search(pattern, low):
            return stat
    return None


def parse_percent(text: str) -> float | None:
    for m in re.finditer(r"([+-]?\d+(?:\.\d+)?)\s*%", text):
        value = float(m.group(1))
        prefix = text[:m.start(1)].rstrip().lower()
        if prefix.endswith("x"):
            # Handle multiplier notation like x1.3% as +30%.
            return value - 1.0
        return value / 100.0

    m = re.search(r"\bx\s*([+-]?\d+(?:\.\d+)?)\b", text, flags=re.IGNORECASE)
    if m:
        # Handle multiplier notation like x1.3 as +30%.
        return float(m.group(1)) - 1.0
    return None


def parse_parenthetical_multiplier(text: str) -> float | None:
    m = re.search(r"\(\s*x\s*([+-]?\d+(?:\.\d+)?)\s+for\s+([^\)]+)\)", text, flags=re.IGNORECASE)
    if not m:
        return None
    multiplier = float(m.group(1))
    if multiplier <= 1.0:
        return None
    return multiplier


def is_conditional_line(text: str) -> bool:
    # Keep stacked effects in the stacks bucket and route trigger-based bonuses to conditional stats.
    low = text.lower()
    if re.search(r"\b(on|upon|while|when|if|after|during)\b", low):
        return True
    return bool(re.search(r"\b(to|against)\s+(sentients?|grineer|corpus|infested|corrupted|murmur)\b", low))


def rank_series(max_value: float, max_rank: int, *, round_digits: int = 3) -> list[float]:
    levels = max_rank + 1
    if levels <= 0:
        return []
    step = max_value / levels
    return [round(step * (i + 1), round_digits) for i in range(levels)]


def bool_series(value: bool, max_rank: int) -> list[bool]:
    return [value for _ in range(max_rank + 1)]


def scaled_series(series: list[float], scale: float, *, round_digits: int = 3) -> list[float]:
    return [round(value * scale, round_digits) for value in series]


@dataclass
class UpgradeParseResult:
    stats: dict
    conditional_stats: dict
    stacks: dict
    max_stacks: int | None


def parse_mod_stats(mod_name: str, mod: dict) -> UpgradeParseResult:
    desc_lines = to_lines(mod.get("Description", ""))
    max_rank = int(mod.get("MaxRank", 0))
    stats = {}
    conditional_stats = {}
    stacks = {}
    max_stacks = None
    last_nonstack_stats = []

    for line in desc_lines:
        low = line.lower()
        if "fire rate cannot be modified" in low:
            stats["fire_rate_lock"] = bool_series(True, max_rank)
            continue
        if "multishot cannot be increased" in low:
            stats["multishot_lock"] = bool_series(True, max_rank)
            continue

        stacks_match = re.search(r"stacks? up to\s*(\d+)x", low)
        extracted = []
        for segment in re.split(r"\band\b", line, flags=re.IGNORECASE):
            val = parse_percent(segment)
            if val is None:
                continue
            stat_key = find_stat_key(segment, mod_name=mod_name)
            if not stat_key:
                continue
            base_series = rank_series(val, max_rank)
            extracted.append((stat_key, base_series))

            conditional_multiplier = parse_parenthetical_multiplier(segment)
            if conditional_multiplier is not None:
                multiplier = conditional_multiplier
                conditional_series = [round(v * (multiplier - 1.0), 3) for v in base_series]
                conditional_stats[stat_key] = conditional_series

        if extracted:
            if stacks_match:
                max_stacks = int(stacks_match.group(1))
                for stat_key, series in extracted:
                    stacks[stat_key] = series
                last_nonstack_stats = []
            else:
                bucket = conditional_stats if is_conditional_line(low) else stats
                for stat_key, series in extracted:
                    bucket[stat_key] = series
                bucket_name = "conditional" if bucket is conditional_stats else "stats"
                last_nonstack_stats = [(bucket_name, stat_key) for stat_key, _ in extracted]
            continue

        if stacks_match and last_nonstack_stats:
            max_stacks = int(stacks_match.group(1))
            for bucket_name, stat_key in last_nonstack_stats:
                source = conditional_stats if bucket_name == "conditional" else stats
                if stat_key in source:
                    stacks[stat_key] = source.pop(stat_key)
            last_nonstack_stats = []

    return UpgradeParseResult(
        stats=stats,
        conditional_stats=conditional_stats,
        stacks=stacks,
        max_stacks=max_stacks,
    )


def build_upgrade_output(parsed: UpgradeParseResult) -> dict | None:
    if not parsed.stats and not parsed.stacks and not parsed.conditional_stats:
        return None

    out = {"stats": parsed.stats}
    if parsed.stacks:
        out["stacks"] = parsed.stacks
        out["max stacks"] = parsed.max_stacks if parsed.max_stacks is not None else 1
    if parsed.conditional_stats:
        out["conditional stats"] = parsed.conditional_stats
    return out


def build_mod_record(mod_name: str, mod: dict) -> dict | None:
    mod_type = str(mod.get("Type", "")).strip().lower()
    if mod_type not in ALLOWED_MOD_TYPES:
        return None
    parsed = parse_mod_stats(mod_name, mod)
    max_rank = int(mod.get("MaxRank", 0))

    mod_set = str(mod.get("Set", "")).lower()
    if "vigilante" in mod_name.lower() or "vigilante" in mod_set:
        parsed.stats["vigilante_bonus"] = [0.05 for _ in range(max_rank + 1)]

    is_sacrificial = "sacrificial" in mod_set
    if is_sacrificial:
        # Sacrificial set bonus is represented as conditional boost to the base stat;
        # ignore the anti-sentient faction line for this project.
        parsed.stats.pop("faction_damage", None)
        parsed.conditional_stats.pop("faction_damage", None)

        if mod_name == "Sacrificial Pressure" and "base_damage" in parsed.stats:
            parsed.conditional_stats["base_damage"] = scaled_series(parsed.stats["base_damage"], 0.25)
        elif mod_name == "Sacrificial Steel" and "crit_chance" in parsed.stats:
            parsed.conditional_stats["crit_chance"] = scaled_series(parsed.stats["crit_chance"], 0.25)

    return build_upgrade_output(parsed)


def build_arcane_record(arcane_name: str, arcane: dict) -> dict | None:
    arcane_type = str(arcane.get("Type", "")).strip().lower()
    if arcane_type not in ALLOWED_ARCANE_TYPES:
        return None
    parsed = parse_mod_stats(arcane_name, arcane)
    return build_upgrade_output(parsed)

# ---------------------------------------------------------------------------
# Top-level builders
# ---------------------------------------------------------------------------

def build_weapons() -> dict[str, dict]:
    wiki_primary   = normalize_lua_lists(fetch_wiki_module("primary"))
    wiki_secondary = normalize_lua_lists(fetch_wiki_module("secondary"))
    wiki_melee     = normalize_lua_lists(fetch_wiki_module("melee"))

    primaries   = {}
    secondaries = {}
    melees      = {}
    skipped = {"primary": 0, "secondary": 0, "melee": 0}

    for name, wiki_weapon in wiki_primary.items():
        entry = build_ranged_record(wiki_weapon)
        if entry is None:
            skipped["primary"] += 1
            continue
        primaries[name] = entry

    for name, wiki_weapon in wiki_secondary.items():
        entry = build_ranged_record(wiki_weapon)
        if entry is None:
            skipped["secondary"] += 1
            continue
        secondaries[name] = entry

    for name, wiki_weapon in wiki_melee.items():
        entry = build_melee_record(wiki_weapon)
        if entry is None:
            skipped["melee"] += 1
            continue
        melees[name] = entry

    primaries   = {n: primaries[n]   for n in sorted(primaries)}
    secondaries = {n: secondaries[n] for n in sorted(secondaries)}
    melees      = {n: melees[n]      for n in sorted(melees)}

    print(f"generated_primaries={len(primaries)}")
    print(f"generated_secondaries={len(secondaries)}")
    print(f"generated_melees={len(melees)}")
    print(f"skipped_primaries={skipped['primary']}")
    print(f"skipped_secondaries={skipped['secondary']}")
    print(f"skipped_melee={skipped['melee']}")

    return {"primary": primaries, "secondary": secondaries, "melee": melees}


def build_upgrades() -> dict[str, dict]:
    mods_data   = normalize_lua_lists(fetch_wiki_module("mods"))
    arcane_data = normalize_lua_lists(fetch_wiki_module("arcane"))

    mods_raw    = mods_data.get("Mods", {})
    arcanes_raw = arcane_data.get("Arcanes", {})

    mods    = {}
    arcanes = {}
    skipped = {"mods": 0, "arcanes": 0}

    for name, mod in mods_raw.items():
        record = build_mod_record(name, mod)
        if not record:
            skipped["mods"] += 1
            continue
        mods[name] = record

    for name, arcane in arcanes_raw.items():
        record = build_arcane_record(name, arcane)
        if not record:
            skipped["arcanes"] += 1
            continue
        arcanes[name] = record

    mods    = {n: mods[n]    for n in sorted(mods)}
    arcanes = {n: arcanes[n] for n in sorted(arcanes)}

    print(f"generated_mods={len(mods)}")
    print(f"generated_arcanes={len(arcanes)}")
    print(f"skipped_mods={skipped['mods']}")
    print(f"skipped_arcanes={skipped['arcanes']}")

    return {"mods": mods, "arcanes": arcanes}


def main() -> None:
    results = {**build_weapons(), **build_upgrades()}
    for key, data in results.items():
        path = OUTPUT_PATHS[key]
        path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote_file={path}")


if __name__ == "__main__":
    main()
