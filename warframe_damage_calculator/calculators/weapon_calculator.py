from collections.abc import Iterator, Mapping
from math import expm1, log1p

from ..fields.attack_result import AttackResult
from ..fields.calculated import AverageStats, CalculatedStats
from ..fields.upgrade import ResolvedStat
from ..fields.weapon_data import Attack
from ..models.build import Build
from ..protocols import BuildUpgradeOwner, ConfigurableWeaponOwner
from ..utils.constants import DOT_MULTIPLIERS
from ..utils.types import Number
from . import helpers


class WeaponCalculator:
    main: AttackResult
    child: list[AttackResult]

    def __init__(self, weapon: ConfigurableWeaponOwner) -> None:
        self.weapon = weapon
        self.recompute()

    def _resolved_build(self) -> ResolvedStat:
        build = Build(*self.weapon.build, *helpers.selected_evolution_upgrades(self.weapon))
        build.stats.resolve(self.weapon.data)
        return build.stats.total.copy()

    def _validate_attack_cycles(self) -> None:
        attacks = self.weapon.data.attacks

        def walk(name: str, ancestors: frozenset[str]) -> None:
            if name in ancestors:
                raise ValueError(f"cyclic attack relationship detected: {name}")
            if name not in attacks:
                return
            next_ancestors = ancestors | {name}
            for child in attacks[name].children:
                walk(child, next_ancestors)

        for name in attacks:
            walk(name, frozenset())

    def _walk_tree(self, name: str, results: Mapping[str, AttackResult], ancestors: frozenset[str] | None = None) -> Iterator[AttackResult]:
        ancestors = frozenset() if ancestors is None else ancestors
        if name in ancestors:
            raise ValueError(f"cyclic attack relationship detected: {name}")
        result = results[name]
        yield result
        next_ancestors = ancestors | {name}
        for child in result.children:
            if child in results:
                yield from self._walk_tree(child, results, next_ancestors)

    def _compute_attack(self, name: str, attack: Attack, resolved_build: ResolvedStat) -> AttackResult:
        result = AttackResult({"name": name, "attack": attack, "build": resolved_build.copy(), "children": list(attack.children)})
        self._compute_base(result)
        self._compute_modded_scalars(result)
        self._apply_condition_overload(result)
        self._compute_modded_damage(result)
        self._compute_effective(result)
        self._compute_average(result)
        return result

    def _compute_base(self, result: AttackResult) -> None:
        attack = result.attack
        ammo, stats = self.weapon.data.ammo, dict(attack.stats)
        stats.update({"attack_speed": attack.stats.fire_rate, "magazine_capacity": ammo.get("magazine_size", 1), "reload_speed": ammo.get("reload_time", 0), "recharge_rate": ammo.get("recharge_rate", 0)})
        result.base = CalculatedStats(self.weapon.stats_type(stats).with_defaults())

    def _compute_modded_scalars(self, result: AttackResult) -> None:
        build, base, modded = result.build, result.base, result.modded
        modded.multiplicative_base_damage = max(1 + build.multiplicative_base_damage, 1)
        modded.base_damage = max(1 + build.base_damage, 0)
        modded.corpus_damage = max(1 + build.corpus_damage, 1)
        modded.grineer_damage = max(1 + build.grineer_damage, 1)
        modded.infested_damage = max(1 + build.infested_damage, 1)
        modded.orokin_damage = max(1 + build.orokin_damage, 1)
        modded.murmur_damage = max(1 + build.murmur_damage, 1)
        modded.sentient_damage = max(1 + build.sentient_damage, 1)
        modded.flat_crit_chance = max(build.flat_crit_chance, 0)
        modded.multiplicative_crit_chance = max(1 + build.multiplicative_crit_chance, 1)
        modded.crit_chance = max(base.crit_chance * (1 + build.crit_chance), 0)
        modded.flat_crit_damage = max(build.flat_crit_damage, 0)
        modded.crit_damage = max(base.crit_damage * (1 + build.crit_damage), 1)
        modded.status_chance = max(base.status_chance * (1 + build.status_chance), 0)
        modded.status_damage = max(1 + build.status_damage, 1)

    def _apply_condition_overload(self, result: AttackResult) -> None:
        bonus = self._average_condition_overload_bonus(result)
        if result.attack.stats.co_effect == "multiplies":
            result.modded.multiplicative_base_damage = max(result.modded.multiplicative_base_damage + bonus, 1)
        else:
            result.modded.base_damage = max(result.modded.base_damage + bonus, 0)

    def _compute_modded_damage(self, result: AttackResult) -> None:
        damage = result.base.damage.apply(result.build.damage).combine().sorted()
        result.modded.damage = result.modded.base_damage * damage

    def _compute_effective(self, result: AttackResult) -> None:
        base, modded, effective = result.base, result.modded, result.effective
        effective.forced_procs = base.forced_procs
        effective.base_damage = modded.base_damage * modded.multiplicative_base_damage
        effective.damage = modded.multiplicative_base_damage * modded.damage
        effective.corpus_damage = modded.corpus_damage
        effective.grineer_damage = modded.grineer_damage
        effective.infested_damage = modded.infested_damage
        effective.orokin_damage = modded.orokin_damage
        effective.murmur_damage = modded.murmur_damage
        effective.sentient_damage = modded.sentient_damage
        effective.crit_chance = modded.crit_chance * modded.multiplicative_crit_chance + modded.flat_crit_chance
        effective.crit_damage = modded.crit_damage + modded.flat_crit_damage
        effective.status_chance = modded.status_chance
        effective.status_damage = modded.status_damage

    def _max_average_faction_damage(self, result: AttackResult) -> float:
        return max(result.average.corpus_damage, result.average.grineer_damage, result.average.infested_damage, result.average.orokin_damage, result.average.murmur_damage, result.average.sentient_damage)

    def _compute_average(self, result: AttackResult) -> None:
        effective, average = result.effective, result.average
        average.crit_chance = effective.crit_chance
        average.crit_multiplier = helpers.crit_multiplier(average.crit_chance, effective.crit_damage)
        average.corpus_damage = effective.corpus_damage
        average.grineer_damage = effective.grineer_damage
        average.infested_damage = effective.infested_damage
        average.orokin_damage = effective.orokin_damage
        average.murmur_damage = effective.murmur_damage
        average.sentient_damage = effective.sentient_damage

    @staticmethod
    def _status_hits(result: AttackResult) -> float:
        build, stats, modded = result.build, result.attack.stats, result.modded
        hits = max(modded.get("multishot", stats.multishot), 1)
        duplicate = modded.get("melee_duplicate", 0)
        chance = max(stats.crit_chance * (1 + build.crit_chance) * modded.multiplicative_crit_chance + modded.flat_crit_chance, 0)
        return hits + duplicate * max(0, 1 - abs(chance - 1))

    def _effective_attacks_per_second(self, result: AttackResult) -> float:
        stats, base, modded = result.attack.stats, result.base, result.modded
        if "attack_speed" in modded:
            return max(stats.fire_rate * modded.attack_speed / (base.attack_speed or 1), 0)
        if "magazine_capacity" not in modded:
            return max(stats.fire_rate, 0)

        build = result.build
        speed = 1 if build.fire_rate_lock else max(1 + build.fire_rate, 0.01)
        fire_rate = max(stats.fire_rate * speed, 0.05) * modded.multiplicative_fire_rate
        burst_count = max(stats.burst_count, 1)
        ammo_cost = max(float(modded.get("ammo_cost", stats.ammo_cost)), 0)
        if ammo_cost <= 0:
            return fire_rate
        shots = modded.magazine_capacity / ammo_cost
        bursts = shots / burst_count
        is_battery = "recharge_delay" in self.weapon.data.ammo
        reload_speed = modded.reload_speed + (0 if not is_battery else float("inf") if modded.recharge_rate <= 0 else modded.magazine_capacity / modded.recharge_rate)
        ammo_spent = 1 - modded.ammo_efficiency
        cycle = bursts * (max(stats.charge_time, 0) / speed / modded.multiplicative_fire_rate + (burst_count - 1) * max(stats.burst_delay, 0) / max(speed, 1))
        cycle += (bursts - ammo_spent) / fire_rate + ammo_spent * reload_speed
        return float("inf") if cycle <= 0 else shots / cycle

    def _average_condition_overload_bonus(self, result: AttackResult, time: Number = 5) -> float:
        build, stats = result.build, result.attack.stats
        damage = stats.damage.apply(build.damage).combine().sorted()
        guaranteed, fractional = divmod(max(stats.status_chance * (1 + build.status_chance), 0), 1)
        guaranteed_hits, fractional_hit = divmod(max(self._status_hits(result), 0), 1)
        probabilities: dict[str, float] = {}
        for damage_type in damage.data:
            weight = damage.weight(damage_type)
            miss = (1 - weight) ** guaranteed * (1 - fractional * weight)
            probabilities[damage_type] = 1 - miss ** guaranteed_hits * (1 - fractional_hit + fractional_hit * miss)
        probabilities.update({damage_type: 1.0 for damage_type, count in stats.forced_procs if count > 0})

        condition_overload = build.condition_overload
        maximum = len(probabilities) if condition_overload.max_stacks == "inf" else int(condition_overload.max_stacks)
        attack_rate = self._effective_attacks_per_second(result)
        if maximum <= 0 or attack_rate <= 0:
            return 0.0
        attempts, distribution = attack_rate * time, [1.0] + [0.0] * maximum
        for probability in probabilities.values():
            acquired = 0 if probability <= 0 else 1 if probability >= 1 else -expm1(attempts * log1p(-probability))
            updated = [0.0] * (maximum + 1)
            for count, chance in enumerate(distribution):
                updated[count] += chance * (1 - acquired)
                updated[min(count + 1, maximum)] += chance * acquired
            distribution = updated
        expected = sum(count * chance for count, chance in enumerate(distribution))
        return float(condition_overload.value) * stats.co_factor * expected

    def _flat_dotph(self, result: AttackResult, *, weakpoint: bool = False, hits: Number | None = None, damage_multiplier: Number = 1, extra_damage: Number = 0, faction_damage: Number | None = None) -> float:
        if faction_damage is None:
            faction_damage = self._max_average_faction_damage(result)
        base, effective, average = result.base, result.effective, result.average
        if effective.damage.total_damage() <= 0:
            return 0.0
        multiplier = average.weakpoint_crit_multiplier if weakpoint else average.crit_multiplier
        regular = sum(factor * effective.damage.get(damage_type) * effective.damage.weight(damage_type) for damage_type, factor in DOT_MULTIPLIERS) * effective.status_chance
        forced = sum(factor * base.forced_procs.get(damage_type) * effective.damage.get(damage_type) for damage_type, factor in DOT_MULTIPLIERS)
        shot_hits = effective.get("multishot", self._status_hits(result)) if hits is None else hits
        return (regular + forced) * effective.status_damage * faction_damage ** 2 * multiplier * damage_multiplier * shot_hits + extra_damage

    def _fold_attack_tree(self, root: AttackResult, tree: list[AttackResult]) -> AverageStats:
        final = root.average.copy()
        final.flat_dph = sum(item.average.get("flat_dph", 0) for item in tree)
        final.flat_dotph = sum(item.average.get("flat_dotph", 0) for item in tree)
        final.total_dph = final.flat_dph + final.flat_dotph

        attack_rate = self._effective_attacks_per_second(root)
        final.flat_dps = final.flat_dph * attack_rate
        final.flat_dotps = final.flat_dotph * attack_rate
        final.total_dps = final.total_dph * attack_rate

        if any("flat_weakpoint_dph" in item.average for item in tree):
            final.flat_weakpoint_dph = sum(item.average.get("flat_weakpoint_dph", 0) for item in tree)
            final.flat_weakpoint_dotph = sum(item.average.get("flat_weakpoint_dotph", 0) for item in tree)
            final.total_weakpoint_dph = final.flat_weakpoint_dph + final.flat_weakpoint_dotph
            final.flat_weakpoint_dps = final.flat_weakpoint_dph * attack_rate
            final.flat_weakpoint_dotps = final.flat_weakpoint_dotph * attack_rate
            final.total_weakpoint_dps = final.total_weakpoint_dph * attack_rate
        return final

    def recompute(self) -> None:
        self._validate_attack_cycles()
        resolved = self._resolved_build()
        results = {name: self._compute_attack(name, attack, resolved) for name, attack in self.weapon.data.attacks.items()}
        for name, result in results.items():
            result.final = self._fold_attack_tree(result, list(self._walk_tree(name, results)))
        self.main = results[self.weapon._attack]
        self.child = [results[name] for name in self.main.children if name in results]

    def contribution(self, upgrade: BuildUpgradeOwner) -> float:
        full = self.weapon.build
        if upgrade not in full:
            return 0.0
        reduced = full - upgrade
        full_dps = self.main.final.total_dps
        try:
            self.weapon.configure(reduced)
            return full_dps - self.main.final.total_dps
        finally:
            self.weapon.configure(full)

    def contribution_values(self) -> dict[str, float]:
        return {str(upgrade.data.name): self.contribution(upgrade) for upgrade in self.weapon.build}

    def contribution_proportions(self) -> dict[str, float]:
        contributions = self.contribution_values()
        total = sum(contributions.values()) or 1
        return {name: contribution / total for name, contribution in contributions.items()}
