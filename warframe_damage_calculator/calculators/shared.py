from typing import Any

from ..models.fields import CalculatedStats
from ..utils.constants import DOT_MULTIPLIERS
from ..utils.functions import expected_distinct_count


def condition_overload_bonus(calculator: Any, mode: Any, duration: float) -> float:
    build = calculator.build.stats.total
    stats = mode.stats
    damage = stats.damage.apply(build.damage).combine().sorted()
    guaranteed, fractional = divmod(max(stats.status_chance * (1 + build.status_chance), 0), 1)
    guaranteed_hits, fractional_hit = divmod(max(calculator._status_hits_for(mode), 0), 1)
    probabilities = {}
    for damage_type in damage.data:
        weight = damage.weight(damage_type)
        miss = (1 - weight) ** guaranteed * (1 - fractional * weight)
        probabilities[damage_type] = 1 - miss ** guaranteed_hits * (1 - fractional_hit + fractional_hit * miss)
    probabilities.update({damage_type: 1.0 for damage_type, count in stats.forced_procs if count > 0})

    condition_overload = build.condition_overload
    maximum = len(probabilities) if condition_overload.max_stacks == "inf" else int(condition_overload.max_stacks)
    attack_rate = calculator._attacks_per_second_for(mode)
    if maximum <= 0 or attack_rate <= 0:
        return 0.0
    expected = expected_distinct_count(probabilities, attack_rate * duration, maximum)
    return float(condition_overload.value) * mode.stats.co_factor * expected


def status_hits(calculator: Any, mode: Any) -> float:
    build = calculator.build.stats.total
    multishot = 1 if build.multishot_lock or "multishot" not in calculator.effective else 1 + build.multishot
    hits = max(mode.stats.multishot * multishot, 1)
    duplicate = calculator.effective.get("melee_duplicate", 0)
    return hits + duplicate * max(0, 1 - abs(calculator._crit_chance_for(mode) - 1))


def attacks_per_second(calculator: Any, mode: Any) -> float:
    if "attack_speed" in calculator.effective:
        return max(mode.stats.fire_rate * calculator.effective.attack_speed / (calculator.base.attack_speed or 1), 0)
    if "magazine_capacity" not in calculator.effective:
        return max(mode.stats.fire_rate, 0)

    build = calculator.build.stats.total
    fire_rate_bonus = 1 if build.fire_rate_lock else max(1 + build.fire_rate, 0.01)
    fire_rate = max(mode.stats.fire_rate * fire_rate_bonus, 0.05) * calculator.modded.multiplicative_fire_rate
    burst_count = max(mode.stats.burst_count, 1)
    bursts = calculator.effective.magazine_capacity / burst_count
    burst_delay = max(mode.stats.burst_delay, 0) / max(fire_rate_bonus, 1)
    charge_time = max(mode.stats.charge_time, 0) / fire_rate_bonus / calculator.modded.multiplicative_fire_rate
    ammo_spent = 1 - calculator.effective.ammo_efficiency
    cycle_time = bursts * (charge_time + (burst_count - 1) * burst_delay) + (bursts - ammo_spent) / fire_rate + ammo_spent * calculator.effective.reload_speed
    return float("inf") if cycle_time <= 0 else calculator.effective.magazine_capacity / cycle_time


def flat_dotph(state: Any, hits: float) -> float:
    regular = sum(multiplier * state.damage.get(damage_type) * state.damage.weight(damage_type) for damage_type, multiplier in DOT_MULTIPLIERS) * state.status_chance
    forced = sum(multiplier * state.forced_procs.get(damage_type) * state.damage.get(damage_type) for damage_type, multiplier in DOT_MULTIPLIERS)
    crit_multiplier = 1 + state.crit_chance * (state.crit_damage - 1)
    return (regular + forced) * state.status_damage * state.faction_damage ** 2 * crit_multiplier * hits


def related_state(calculator: Any, mode: Any) -> tuple[CalculatedStats, CalculatedStats]:
    build = calculator.build.stats.total
    base = CalculatedStats(mode.stats.with_defaults())
    co_bonus = calculator._average_condition_overload_bonus_for(mode)
    additive = max(1 + build.base_damage + (co_bonus if mode.stats.co_effect != "multiplies" else 0), 0)
    multiplicative = max(1 + build.multiplicative_base_damage + (co_bonus if mode.stats.co_effect == "multiplies" else 0), 1)
    crit_chance = calculator._crit_chance_for(mode)
    effective = CalculatedStats({
        "damage": additive * multiplicative * base.damage.apply(build.damage).combine().sorted(),
        "forced_procs": base.forced_procs,
        "faction_damage": calculator.effective.faction_damage,
        "crit_chance": crit_chance,
        "crit_damage": max(base.crit_damage * (1 + build.crit_damage) + calculator.modded.flat_crit_damage, 1),
        "status_chance": max(base.status_chance * (1 + build.status_chance), 0),
        "status_damage": calculator.effective.status_damage,
        "multishot": calculator._status_hits_for(mode),
        "weakpoint_damage": calculator.effective.get("weakpoint_damage", 1),
        "weakpoint_crit_chance": crit_chance + max(base.crit_chance * build.weakpoint_crit_chance, 0),
    })
    return base, effective
