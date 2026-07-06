import streamlit as st

from warframe_damage_calculator import Build, Melee, Primary, Secondary, Upgrade, dist

# py -m streamlit run web/app.py

WEAPON_TYPES = {
    "Melee": Melee,
    "Primary": Primary,
    "Secondary": Secondary,
}

DAMAGE_TYPES = (
    "impact",
    "puncture",
    "slash",
    "cold",
    "electricity",
    "heat",
    "toxin",
    "blast",
    "corrosive",
    "gas",
    "magnetic",
    "radiation",
    "viral",
    "void",
)

DEFAULT_DAMAGE_TYPES = ("impact", "puncture", "slash")

MOD_FIELD_OPTIONS = (
    "damage_dist",
    "base_damage",
    "multiplicative_base_damage",
    "faction_damage",
    "weakpoint_damage",
    "attack_speed",
    "multiplicative_fire_rate",
    "fire_rate",
    "reload_speed",
    "magazine_capacity",
    "ammo_efficiency",
    "multishot",
    "flat_crit_chance",
    "multiplicative_crit_chance",
    "crit_chance",
    "multiplicative_weakpoint_crit_chance",
    "weakpoint_crit_chance",
    "flat_crit_damage",
    "crit_damage",
    "status_chance",
    "status_damage",
    "hunter_munitions",
    "internal_bleeding",
    "primed_chamber",
    "vigilante_bonus",
)

ARCANE_FIELD_OPTIONS = (
    "secondary_enervate",
    "secondary_encumber",
    "melee_duplicate",
    "melee_doughty",
)

ARCANE_FIELD_OPTIONS_BY_WEAPON = {
    "Melee": ("melee_duplicate", "melee_doughty"),
    "Primary": (),
    "Secondary": ("secondary_enervate", "secondary_encumber"),
}

FIELD_WEAPON_RULES = {
    "ammo_efficiency": {"Primary", "Secondary"},
    "burst_count": {"Primary", "Secondary"},
    "burst_delay": {"Primary", "Secondary"},
    "charge_time": {"Primary", "Secondary"},
    "fire_rate": {"Primary", "Secondary"},
    "magazine_capacity": {"Primary", "Secondary"},
    "reload_speed": {"Primary", "Secondary"},
    "weakpoint_damage": {"Primary", "Secondary"},
    "multiplicative_fire_rate": {"Primary", "Secondary"},
    "multiplicative_weakpoint_crit_chance": {"Primary", "Secondary"},
    "weakpoint_crit_chance": {"Primary", "Secondary"},
    "is_beam": {"Primary", "Secondary"},
    "is_battery": {"Primary", "Secondary"},
    "attack_speed": {"Melee"},
    "melee_duplicate": {"Melee"},
    "melee_doughty": {"Melee"},
    "secondary_enervate": {"Primary", "Secondary"},
    "secondary_encumber": {"Primary", "Secondary"},
}


def field_label(field_name: str) -> str:
    return field_name.replace("_", " ").title()


def is_field_allowed(field_name: str, weapon_type_name: str) -> bool:
    allowed_weapon_types = FIELD_WEAPON_RULES.get(field_name)
    return allowed_weapon_types is None or weapon_type_name in allowed_weapon_types


def allowed_fields(field_names: tuple[str, ...], weapon_type_name: str) -> list[str]:
    return [field_name for field_name in field_names if is_field_allowed(field_name, weapon_type_name)]


def arcane_fields_for_weapon(weapon_type_name: str) -> list[str]:
    return list(ARCANE_FIELD_OPTIONS_BY_WEAPON.get(weapon_type_name, ()))


ARCANE_FIELD_LIMITS = {
    "secondary_enervate": (0, 6),
    "secondary_encumber": (0.0, 0.24),
    "melee_duplicate": (0.0, 1.0),
    "melee_doughty": (0.0, 1.0),
}


def float_input(
    label: str,
    *,
    value: float = 0.0,
    min_value: float | None = None,
    max_value: float | None = None,
    step: float = 0.001,
    key: str | None = None,
) -> float:
    return st.number_input(
        label,
        value=value,
        min_value=min_value,
        max_value=max_value,
        step=step,
        format="%.3f",
        key=key,
    )


def ui_damage_dist(title: str, key_prefix: str, defaults: tuple[str, ...] = DEFAULT_DAMAGE_TYPES) -> dist:
    st.markdown(f"**{title}**")
    selected_types = st.multiselect(
        "Damage Types",
        DAMAGE_TYPES,
        default=defaults,
        key=f"{key_prefix}_selected_types",
    )

    values: dict[str, float] = {}
    for damage_type in selected_types:
        values[damage_type] = float_input(field_label(damage_type), min_value=0.0, value=0.0, key=f"{key_prefix}_{damage_type}")

    return dist(**{name: value for name, value in values.items() if value > 0})


def ui_base_weapon_stats(weapon_type_name: str) -> dict:
    st.subheader("Base Stats")
    stats = {}

    with st.expander("Direct Hit", expanded=True):
        stats["damage_dist"] = ui_damage_dist("Base Damage", "base_damage")
        stats["forced_procs"] = ui_damage_dist("Base Forced Procs", "forced_procs", defaults=())

    if weapon_type_name != "Melee":
        with st.expander("Explosion", expanded=False):
            stats["explosion_damage_dist"] = ui_damage_dist("Explosion Damage", "explosion_damage", defaults=())
            stats["explosion_forced_procs"] = ui_damage_dist("Explosion Forced Procs", "explosion_forced_procs", defaults=())

    if weapon_type_name == "Melee":
        col1, col2 = st.columns(2)
        with col1:
            stats["crit_chance"] = float_input("Crit Chance", min_value=0.0, max_value=10.0, value=0.0)
            stats["crit_damage"] = float_input("Crit Damage", min_value=1.0, max_value=20.0, value=1.0)
        with col2:
            stats["status_chance"] = float_input("Status Chance", min_value=0.0, max_value=10.0, value=0.0)
            stats["attack_speed"] = float_input("Attack Speed", min_value=0.0, max_value=20.0, value=1.0)
    else:
        stats["is_beam"] = st.checkbox("Beam Weapon", value=False)
        stats["is_battery"] = st.checkbox("Battery Weapon", value=False)

        col1, col2 = st.columns(2)
        with col1:
            stats["crit_chance"] = float_input("Crit Chance", min_value=0.0, max_value=10.0, value=0.0)
            stats["crit_damage"] = float_input("Crit Damage", min_value=1.0, max_value=20.0, value=1.0)
            stats["status_chance"] = float_input("Status Chance", min_value=0.0, max_value=10.0, value=0.0)
            stats["multishot"] = float_input("Multishot", min_value=1.0, max_value=100.0, value=1.0)
            stats["burst_count"] = st.number_input("Burst Count", min_value=1, max_value=100, value=1, step=1)
            stats["burst_delay"] = float_input("Burst Delay", min_value=0.0, max_value=20.0, value=0.0)
        with col2:
            stats["weakpoint_damage"] = float_input("Weakpoint Damage", min_value=1.0, max_value=20.0, value=3.0)
            stats["magazine_capacity"] = st.number_input("Magazine Capacity", min_value=1, max_value=10000, value=1, step=1)
            stats["fire_rate"] = float_input("Fire Rate", min_value=0.05, max_value=100.0, value=0.05)
            stats["reload_speed"] = float_input("Reload Speed", min_value=0.0, max_value=20.0, value=0.0)
            stats["charge_time"] = float_input("Charge Time", min_value=0.0, max_value=20.0, value=0.0)
            stats["recharge_rate"] = float_input("Recharge Rate", min_value=0.0, max_value=1000.0, value=0.0)
            
    if weapon_type_name == "Melee":
        stats["attack_speed"] = stats.get("attack_speed", 1.0)
    else:
        stats.setdefault("fire_rate", 1.0)
        stats.setdefault("burst_count", 1)
        stats.setdefault("charge_time", 0.0)
        stats.setdefault("recharge_rate", 0.0)
        stats.setdefault("weakpoint_damage", 3.0)
        stats.setdefault("multishot", 1.0)
        stats.setdefault("burst_delay", 0.0)
        stats.setdefault("reload_speed", 0.0)
        stats.setdefault("magazine_capacity", 1)
        stats.setdefault("is_beam", False)
        stats.setdefault("is_battery", False)
        stats.setdefault("explosion_damage_dist", dist())
        stats.setdefault("explosion_forced_procs", dist())

    return stats


def ui_upgrade(section_name: str, item_label: str, key_prefix: str, weapon_type_name: str, *, allow_negative: bool, single_arcane: bool = False) -> Upgrade:
    expander_title = section_name if not item_label else f"{section_name}: {item_label}"
    with st.expander(expander_title, expanded=False):
        if single_arcane:
            arcane_fields = arcane_fields_for_weapon(weapon_type_name)
            selected_field = st.selectbox(
                "Choose Effect",
                ["None", *arcane_fields],
                format_func=lambda value: field_label(value) if value != "None" else "None",
                key=f"{key_prefix}_selected_field",
            )
            selected_fields = [] if selected_field == "None" else [selected_field]
        else:
            mod_fields = allowed_fields(MOD_FIELD_OPTIONS, weapon_type_name)
            selected_fields = st.multiselect(
                "Choose Effects",
                mod_fields,
                default=["damage_dist"],
                key=f"{key_prefix}_selected_fields",
            )

        values: dict[str, float | int | dist] = {}

        for field_name in selected_fields:
            if field_name == "damage_dist":
                values[field_name] = ui_damage_dist("Element / Damage Bonus", f"{key_prefix}_damage", defaults=())
            elif field_name == "attack_speed" and weapon_type_name == "Melee":
                values[field_name] = float_input(
                    field_label(field_name),
                    min_value=-100.0 if allow_negative else 0.0,
                    max_value=100.0,
                    value=0.0,
                    key=f"{key_prefix}_{field_name}",
                )
            elif field_name == "secondary_enervate":
                values[field_name] = st.number_input(
                    field_label(field_name),
                    min_value=0,
                    max_value=6,
                    value=0,
                    step=1,
                    key=f"{key_prefix}_{field_name}",
                )
            elif field_name == "magazine_capacity":
                values[field_name] = st.number_input(
                    field_label(field_name),
                    min_value=-1000 if allow_negative else 0,
                    max_value=1000,
                    value=0,
                    step=1,
                    key=f"{key_prefix}_{field_name}",
                )
            elif field_name in ARCANE_FIELD_OPTIONS:
                arcane_min, arcane_max = ARCANE_FIELD_LIMITS[field_name]
                arcane_value = float_input(field_label(field_name), min_value=arcane_min, max_value=arcane_max, value=0.0, key=f"{key_prefix}_{field_name}")
                values[field_name] = int(arcane_value) if field_name == "secondary_enervate" else arcane_value
            elif field_name == "ammo_efficiency":
                values[field_name] = float_input(
                    field_label(field_name),
                    min_value=-0.999 if allow_negative else 0.0,
                    max_value=0.999,
                    value=0.0,
                    key=f"{key_prefix}_{field_name}",
                )
            else:
                values[field_name] = float_input(
                    field_label(field_name),
                    min_value=-100.0 if allow_negative else 0.0,
                    max_value=100.0,
                    value=0.0,
                    key=f"{key_prefix}_{field_name}",
                )

        upgrade_kwargs: dict[str, object] = {
            "damage_dist": values.get("damage_dist", dist()),
            "base_damage": float(values.get("base_damage", 0.0)),
            "faction_damage": float(values.get("faction_damage", 0.0)),
            "crit_chance": float(values.get("crit_chance", 0.0)),
            "crit_damage": float(values.get("crit_damage", 0.0)),
            "status_chance": float(values.get("status_chance", 0.0)),
            "status_damage": float(values.get("status_damage", 0.0)),
            "weakpoint_damage": float(values.get("weakpoint_damage", 0.0)),
            "reload_speed": float(values.get("reload_speed", 0.0)),
            "fire_rate": float(values.get("fire_rate", 0.0)),
            "multishot": float(values.get("multishot", 0.0)),
            "attack_speed": float(values.get("attack_speed", 0.0)),
            "hunter_munitions": float(values.get("hunter_munitions", 0.0)),
            "internal_bleeding": float(values.get("internal_bleeding", 0.0)),
            "primed_chamber": float(values.get("primed_chamber", 0.0)),
            "vigilante_bonus": float(values.get("vigilante_bonus", 0.0)),
            "multiplicative_base_damage": float(values.get("multiplicative_base_damage", 0.0)),
            "multiplicative_fire_rate": float(values.get("multiplicative_fire_rate", 0.0)),
            "flat_crit_chance": float(values.get("flat_crit_chance", 0.0)),
            "multiplicative_crit_chance": float(values.get("multiplicative_crit_chance", 0.0)),
            "weakpoint_crit_chance": float(values.get("weakpoint_crit_chance", 0.0)),
            "multiplicative_weakpoint_crit_chance": float(values.get("multiplicative_weakpoint_crit_chance", 0.0)),
            "flat_crit_damage": float(values.get("flat_crit_damage", 0.0)),
            "ammo_efficiency": float(values.get("ammo_efficiency", 0.0)),
            "magazine_capacity": float(values.get("magazine_capacity", 0.0)),
        }

        if single_arcane:
            upgrade_kwargs.update(
                secondary_enervate=int(values.get("secondary_enervate", 0)),
                secondary_encumber=float(values.get("secondary_encumber", 0.0)),
                melee_duplicate=float(values.get("melee_duplicate", 0.0)),
                melee_doughty=float(values.get("melee_doughty", 0.0)),
            )

        return Upgrade(**upgrade_kwargs)


def render_section_header(title: str, count: int) -> None:
    if count > 0:
        st.header(title)


def is_non_empty_upgrade(item: Upgrade) -> bool:
    if any(value != 0 for _, value in item.damage_dist):
        return True

    scalar_fields = (
        item.base_damage,
        item.faction_damage,
        item.crit_chance,
        item.crit_damage,
        item.status_chance,
        item.status_damage,
        item.weakpoint_damage,
        item.reload_speed,
        item.fire_rate,
        item.multishot,
        item.attack_speed,
        item.hunter_munitions,
        item.internal_bleeding,
        item.primed_chamber,
        item.vigilante_bonus,
        item.multiplicative_base_damage,
        item.multiplicative_fire_rate,
        item.flat_crit_chance,
        item.multiplicative_crit_chance,
        item.weakpoint_crit_chance,
        item.multiplicative_weakpoint_crit_chance,
        item.flat_crit_damage,
        item.ammo_efficiency,
        item.magazine_capacity,
        item.secondary_enervate,
        item.secondary_encumber,
        item.melee_duplicate,
        item.melee_doughty,
    )
    return any(value != 0 for value in scalar_fields)


st.set_page_config(page_title="Warframe Damage Calculator", layout="wide")
st.title("Warframe Damage Calculator")
st.caption("Deterministic base-weapon and build calculations")

with st.sidebar:
    st.header("Weapon")
    selected_weapon_type_name = st.selectbox("Type", list(WEAPON_TYPES))
    selected_weapon_type = WEAPON_TYPES[selected_weapon_type_name]

    st.header("Build")
    mod_count = st.slider("Mods", min_value=0, max_value=8, value=0, step=1)
    extra_buff_count = st.slider("Extra Buffs", min_value=0, max_value=6, value=0, step=1)

base_stats = ui_base_weapon_stats(selected_weapon_type_name)

upgrades: list[Upgrade] = []

render_section_header("Mods", mod_count)
for i in range(mod_count):
    mod = ui_upgrade("Mod", f"#{i + 1}", f"mod_{i}", selected_weapon_type_name, allow_negative=True)
    if is_non_empty_upgrade(mod):
        upgrades.append(mod)

st.header("Arcane")
arcane = ui_upgrade("Arcane", "", "arcane", selected_weapon_type_name, allow_negative=False, single_arcane=True)
if is_non_empty_upgrade(arcane):
    upgrades.append(arcane)

render_section_header("External Buffs", extra_buff_count)
for i in range(extra_buff_count):
    buff = ui_upgrade("Buff", f"#{i + 1}", f"buff_{i}", selected_weapon_type_name, allow_negative=False)
    if is_non_empty_upgrade(buff):
        upgrades.append(buff)

weapon = selected_weapon_type(**base_stats)
if upgrades:
    weapon.configure(Build(*upgrades))

st.subheader("Results")
stats = weapon.stats

metric_cols = st.columns(6)

metric_cols[0].metric("Flat DPH", f"{stats.flat_dph:,.2f}")
metric_cols[1].metric("Flat DOTPH", f"{stats.flat_dotph:,.2f}")
metric_cols[2].metric("Total DPH", f"{stats.total_dph:,.2f}")
metric_cols[3].metric("Flat DPS", f"{stats.flat_dps:,.2f}")
metric_cols[4].metric("Flat DOTPS", f"{stats.flat_dotps:,.2f}")
metric_cols[5].metric("Total DPS", f"{stats.total_dps:,.2f}")

if selected_weapon_type_name in ("Primary", "Secondary"):
    metric_cols[0].metric("Flat Weakpoint DPH", f"{stats.flat_weakpoint_dph:,.2f}")
    metric_cols[1].metric("Flat Weakpoint DOTPH", f"{stats.flat_weakpoint_dotph:,.2f}")
    metric_cols[2].metric("Total Weakpoint DPH", f"{stats.total_weakpoint_dph:,.2f}")
    metric_cols[3].metric("Flat Weakpoint DPS", f"{stats.flat_weakpoint_dps:,.2f}")
    metric_cols[4].metric("Flat Weakpoint DOTPS", f"{stats.flat_weakpoint_dotps:,.2f}")
    metric_cols[5].metric("Total Weakpoint DPS", f"{stats.total_weakpoint_dps:,.2f}")

    ranged_cols = st.columns(6)
    ranged_cols[0].metric("Average Fire Rate", f"{stats.average_fire_rate:,.2f}")
    ranged_cols[1].metric("Procs / Shot", f"{stats.average_procs_per_shot:,.2f}")

with st.expander("Effective Damage Distribution", expanded=True):
    effective_rows = [{"Damage Type": dt.title(), "Damage": dmg, "Weight": stats.effective.damage_dist.weight(dt), "Procs Per Shot": stats.effective.damage_dist.weight(dt)*stats.effective.status_chance*stats.effective.multishot} for dt, dmg in stats.effective.damage_dist]
    if effective_rows:
        st.dataframe(effective_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No positive damage values set.")

with st.expander("Text Summary", expanded=False):
    st.code(weapon.format.summary(), language="text")

