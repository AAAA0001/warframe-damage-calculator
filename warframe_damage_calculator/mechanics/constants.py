DOT_MULTIPLIERS = (("slash", 2.1), ("heat", 3.0), ("toxin", 3.0), ("electricity", 3.0), ("gas", 3.0))

PHYSICAL = {"impact", "puncture", "slash"}
ELEMENTAL = {"cold", "electricity", "heat", "toxin"}
ELEMENTAL_COMBINATIONS = {("cold", "heat"): "blast", ("electricity", "toxin"): "corrosive", ("heat", "toxin"): "gas", ("cold", "electricity"): "magnetic", ("electricity", "heat"): "radiation", ("cold", "toxin"): "viral"}
DAMAGE_TYPES = ("impact", "puncture", "slash", "blast", "corrosive", "gas", "magnetic", "radiation", "viral", "cold", "electricity", "heat", "toxin")
DAMAGE_TYPE_ORDER = dict(enumerate(DAMAGE_TYPES))

WEAPON_TABLES = ("primary", "secondary", "melee")
UPGRADE_TABLES = ("mod", "arcane")