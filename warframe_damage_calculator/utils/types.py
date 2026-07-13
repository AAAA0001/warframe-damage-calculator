from typing import Literal, TypeAlias, get_args

DamageType: TypeAlias = Literal["impact", "puncture", "slash", "blast", "corrosive", "gas", "magnetic", "radiation", "viral", "cold", "electricity", "heat", "toxin", "void"]

_ModifierStat: TypeAlias = Literal["damage", "multiplicative_base_damage", "base_damage", "faction_damage", "status_damage", "flat_crit_chance", "multiplicative_crit_chance", "crit_chance", "flat_crit_damage", "crit_damage", "status_chance", "weakpoint_damage", "multiplicative_weakpoint_crit_chance", "weakpoint_crit_chance", "multiplicative_fire_rate", "fire_rate", "fire_rate_lock", "reload_speed", "ammo_efficiency", "magazine_capacity", "multishot", "multishot_lock", "internal_bleeding", "hunter_munitions", "primed_chamber", "vigilante_bonus", "secondary_enervate", "secondary_encumber", "attack_speed", "melee_duplicate", "melee_doughty"]
Stat: TypeAlias = DamageType | _ModifierStat

Value: TypeAlias = float | int | bool
Condition: TypeAlias = str

VALID_STATS = frozenset((*get_args(DamageType), *get_args(_ModifierStat)))
