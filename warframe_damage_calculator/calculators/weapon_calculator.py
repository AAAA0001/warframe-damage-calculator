from math import expm1, log1p
from typing import Any

from ..models.build import Build
from ..models.fields import AverageStats, CalculatedStats
from ..models.upgrade import Upgrade
from ..utils.constants import DOT_MULTIPLIERS


class WeaponCalculator:
    CONDITION_OVERLOAD_DURATION = 5.0

    def __init__(self, weapon: Any) -> None:
        self.weapon = weapon
        self.build = Build()
        self.base = CalculatedStats()
        self.modded = CalculatedStats()
        self.effective = CalculatedStats()
        self.average = AverageStats()
        self.recompute()

    def _compute_modded_stats(self) -> None:
        build = self.build.stats.total
        damage = self.base.damage.apply(build.damage).combine().sorted()
        faction_damage = max(build.corpus_damage, build.grineer_damage, build.infested_damage, build.orokin_damage, build.murmur_damage, build.sentient_damage)

        self.modded.multiplicative_base_damage = max(1 + build.multiplicative_base_damage, 1)
        self.modded.base_damage = max(1 + build.base_damage, 0)
        self.modded.damage = self.modded.base_damage * damage
        self.modded.faction_damage = max(1 + faction_damage, 1)
        self.modded.flat_crit_chance = max(build.flat_crit_chance, 0)
        self.modded.multiplicative_crit_chance = max(1 + build.multiplicative_crit_chance, 1)
        self.modded.crit_chance = max(self.base.crit_chance * (1 + build.crit_chance), 0)
        self.modded.flat_crit_damage = max(build.flat_crit_damage, 0)
        self.modded.crit_damage = max(self.base.crit_damage * (1 + build.crit_damage), 1)
        self.modded.status_chance = max(self.base.status_chance * (1 + build.status_chance), 0)
        self.modded.status_damage = max(1 + build.status_damage, 1)

    def _compute_effective_stats(self) -> None:
        self.effective.forced_procs = self.base.forced_procs
        self.effective.base_damage = self.modded.base_damage * self.modded.multiplicative_base_damage
        self.effective.damage = self.modded.multiplicative_base_damage * self.modded.damage
        self.effective.faction_damage = self.modded.faction_damage
        self.effective.crit_chance = self.modded.crit_chance * self.modded.multiplicative_crit_chance + self.modded.flat_crit_chance
        self.effective.crit_damage = self.modded.crit_damage + self.modded.flat_crit_damage
        self.effective.status_chance = self.modded.status_chance
        self.effective.status_damage = self.modded.status_damage

    def _compute_average_stats(self) -> None:
        self._compute_related_attacks()
        self.average.crit_chance = self.effective.crit_chance
        self.average.crit_multiplier = 1 + self.average.crit_chance * (self.effective.crit_damage - 1)

    def _condition_overload_bonus_for(self, status_probabilities: dict[str, float], attacks_per_second: float, mode: Any) -> float:
        condition_overload = self.build.stats.total.condition_overload
        max_stacks = len(status_probabilities) if condition_overload.max_stacks == "inf" else int(condition_overload.max_stacks)
        if max_stacks <= 0 or attacks_per_second <= 0:
            return 0.0

        attempts = attacks_per_second * self.CONDITION_OVERLOAD_DURATION
        stacks = [1.0] + [0.0] * max_stacks
        for probability in status_probabilities.values():
            if probability <= 0:
                continue
            acquired = 1.0 if probability >= 1 else -expm1(attempts * log1p(-probability))
            updated = [0.0] * (max_stacks + 1)
            for count, state_probability in enumerate(stacks):
                updated[count] += state_probability * (1 - acquired)
                updated[min(count + 1, max_stacks)] += state_probability * acquired
            stacks = updated

        expected_stacks = sum(count * probability for count, probability in enumerate(stacks))
        return float(condition_overload.value) * mode.stats.co_factor * expected_stacks

    def _average_condition_overload_bonus_for(self, mode: Any) -> float:
        build = self.build.stats.total
        stats = mode.stats
        damage = stats.damage.apply(build.damage).combine().sorted()
        guaranteed, fractional = divmod(max(stats.status_chance * (1 + build.status_chance), 0), 1)
        guaranteed_hits, fractional_hit = divmod(max(self._status_hits_for(mode), 0), 1)
        probabilities = {}
        for damage_type in damage.data:
            weight = damage.weight(damage_type)
            miss = (1 - weight) ** guaranteed * (1 - fractional * weight)
            miss = miss ** guaranteed_hits * (1 - fractional_hit + fractional_hit * miss)
            probabilities[damage_type] = 1 - miss
        for damage_type, count in stats.forced_procs:
            if count > 0:
                probabilities[damage_type] = 1.0
        return self._condition_overload_bonus_for(probabilities, self._attacks_per_second_for(mode), mode)

    def _status_hits_for(self, mode: Any) -> float:
        build = self.build.stats.total
        multishot_multiplier = self.effective.get("multishot", 1) / (self.base.get("multishot", 1) or 1)
        hits = max(mode.stats.multishot * multishot_multiplier, 1)
        crit_chance = max(mode.stats.crit_chance * (1 + build.crit_chance) * self.modded.multiplicative_crit_chance + self.modded.flat_crit_chance, 0)
        return hits + self.effective.get("melee_duplicate", 0) * max(0, 1 - abs(crit_chance - 1))

    def _attacks_per_second_for(self, mode: Any) -> float:
        if "attack_speed" in self.effective: return max(mode.stats.fire_rate * self.effective.attack_speed / (self.base.attack_speed or 1), 0)
        if "magazine_capacity" not in self.effective: return max(mode.stats.fire_rate, 0)
        build = self.build.stats.total
        fire_rate_bonus = 1 if build.fire_rate_lock else max(1 + build.fire_rate, 0.01)
        fire_rate = max(mode.stats.fire_rate * fire_rate_bonus, 0.05) * self.modded.multiplicative_fire_rate
        burst_count = max(mode.stats.burst_count, 1)
        bursts = self.effective.magazine_capacity / burst_count
        burst_delay = max(mode.stats.burst_delay, 0) / max(fire_rate_bonus, 1)
        charge_time = max(mode.stats.charge_time, 0) / fire_rate_bonus / self.modded.multiplicative_fire_rate
        ammo_spent = 1 - self.effective.ammo_efficiency
        cycle_time = bursts * (charge_time + (burst_count - 1) * burst_delay) + (bursts - ammo_spent) / fire_rate + ammo_spent * self.effective.reload_speed
        return float("inf") if cycle_time <= 0 else self.effective.magazine_capacity / cycle_time

    def _compute_related_attacks(self) -> None:
        self.related_base: dict[str, CalculatedStats] = {}
        self.related: dict[str, CalculatedStats] = {}
        build = self.build.stats.total
        for name in self.weapon.mode.get("children", []):
            mode = self.weapon.data.entry.attacks.get(name)
            if mode is None:
                continue
            display_name = name.replace("_", " ").title()
            base = CalculatedStats(mode.stats.with_defaults())
            co_bonus = self._average_condition_overload_bonus_for(mode)
            additive = max(1 + build.base_damage + (co_bonus if mode.stats.co_effect != "multiplies" else 0), 0)
            multiplicative = max(1 + build.multiplicative_base_damage + (co_bonus if mode.stats.co_effect == "multiplies" else 0), 1)
            crit_chance = max(base.crit_chance * (1 + build.crit_chance) * self.modded.multiplicative_crit_chance + self.modded.flat_crit_chance, 0)

            self.related_base[display_name] = base
            self.related[display_name] = CalculatedStats({
                "damage": additive * multiplicative * base.damage.apply(build.damage).combine().sorted(),
                "forced_procs": base.forced_procs,
                "faction_damage": self.effective.faction_damage,
                "crit_chance": crit_chance,
                "crit_damage": max(base.crit_damage * (1 + build.crit_damage) + self.modded.flat_crit_damage, 1),
                "status_chance": max(base.status_chance * (1 + build.status_chance), 0),
                "status_damage": self.effective.status_damage,
                "multishot": self._status_hits_for(mode),
                "weakpoint_damage": self.effective.get("weakpoint_damage", 1),
                "weakpoint_crit_chance": crit_chance + max(base.crit_chance * build.weakpoint_crit_chance, 0),
            })

    def _related_dotph(self) -> float:
        return sum((sum(multiplier * state.damage.get(damage_type) * state.damage.weight(damage_type) for damage_type, multiplier in DOT_MULTIPLIERS) * state.status_chance + sum(multiplier * state.forced_procs.get(damage_type) * state.damage.get(damage_type) for damage_type, multiplier in DOT_MULTIPLIERS)) * (1 + state.crit_chance * (state.crit_damage - 1)) * state.status_damage * state.faction_damage ** 2 * state.multishot for state in self.related.values())

    def _load_base_stats(self) -> None:
        stats = dict(self.weapon.mode.stats)
        ammo = self.weapon.data.entry.ammo
        stats.update({"magazine_capacity": ammo.get("magazine_size", 1), "reload_speed": ammo.get("reload_time", 0), "recharge_rate": ammo.get("recharge_rate", 0)})
        if self.weapon.data.entry.type == "melee":
            stats["attack_speed"] = self.weapon.mode.stats.fire_rate
        self.base = CalculatedStats(self.weapon.mode_stats_type(stats).with_defaults())

    def _resolve_build(self) -> None:
        evolutions = (Upgrade({f"{evolution} perk {perk}": {"type": "evolution", "max_rank": 0, "compatibility": {"types": []}, "stats": self.weapon.data.entry.evolutions[evolution.removeprefix("evolution_")][str(perk)].get("stats", {})}}) for evolution, perk in self.weapon.evolutions.items())
        self.build = Build(*self.weapon.build, *evolutions)
        entry = self.weapon.data.entry
        context = {"name": self.weapon.data.name, "type": entry.type, "subtype": entry.subtype, "trigger": self.weapon.mode.get("trigger"), "projectile": self.weapon.mode.get("delivery"), "aoe": self.weapon.mode.get("aoe", False)}
        self.build.stats.resolve({"context": context})

    def _apply_condition_overload(self) -> None:
        co_bonus = self._average_condition_overload_bonus_for(self.weapon.mode)
        if self.weapon.mode.stats.co_effect == "multiplies":
            self.modded.multiplicative_base_damage = max(self.modded.multiplicative_base_damage + co_bonus, 1)
        else:
            self.modded.base_damage = max(self.modded.base_damage + co_bonus, 0)
        damage = self.base.damage.apply(self.build.stats.total.damage).combine().sorted()
        self.modded.damage = self.modded.base_damage * damage
        self.effective.base_damage = self.modded.base_damage * self.modded.multiplicative_base_damage
        self.effective.damage = self.modded.multiplicative_base_damage * self.modded.damage

    def recompute(self) -> None:
        self._resolve_build()
        self._load_base_stats()
        self._compute_modded_stats()
        self._compute_effective_stats()
        self._apply_condition_overload()
        self._compute_average_stats()

    def contribution(self, upgrade: Upgrade) -> float:
        full = self.weapon.build
        if all(equipped.data != upgrade.data for equipped in full):
            return 0.0
        reduced = full - upgrade
        full_dps = self.average.total_dps
        try:
            self.weapon.configure(reduced)
            return full_dps - self.average.total_dps
        finally:
            self.weapon.configure(full)

    def contribution_values(self) -> dict[str, float]:
        return {str(upgrade.data.name): self.contribution(upgrade) for upgrade in self.weapon.build}

    def contribution_proportions(self) -> dict[str, float]:
        contributions = self.contribution_values()
        total = sum(contributions.values()) or 1
        return {name: contribution / total for name, contribution in contributions.items()}
