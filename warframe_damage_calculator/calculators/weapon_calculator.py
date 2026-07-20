from typing import Any

from ..models.build import Build
from ..models.fields import AverageStats, CalculatedStats
from ..models.upgrade import Upgrade
from .shared import attacks_per_second, condition_overload_bonus, flat_dotph, related_state, status_hits


class WeaponCalculator:
    def __init__(self, weapon: Any) -> None:
        self.weapon = weapon
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
        self.average.crit_chance = self.effective.crit_chance
        self.average.crit_multiplier = 1 + self.average.crit_chance * (self.effective.crit_damage - 1)

    def _average_condition_overload_bonus_for(self, mode: Any) -> float:
        return condition_overload_bonus(self, mode, 5.0)

    def _status_hits_for(self, mode: Any) -> float:
        return status_hits(self, mode)

    def _crit_chance_for(self, mode: Any) -> float:
        build = self.build.stats.total
        return max(mode.stats.crit_chance * (1 + build.crit_chance) * self.modded.multiplicative_crit_chance + self.modded.flat_crit_chance, 0)

    def _attacks_per_second_for(self, mode: Any) -> float:
        return attacks_per_second(self, mode)

    def _compute_related_attacks(self) -> None:
        self.related_base: dict[str, CalculatedStats] = {}
        self.related: dict[str, CalculatedStats] = {}
        for name in self.weapon.mode.get("children", []):
            mode = self.weapon.data.entry.attacks[name]
            display_name = name.replace("_", " ").title()
            self.related_base[display_name], self.related[display_name] = related_state(self, mode)

    def _related_dotph(self) -> float:
        return sum(self._flat_dotph_for_state(state) for state in self.related.values())

    def _flat_dotph_for_state(self, state: CalculatedStats) -> float:
        return flat_dotph(state, state.get("multishot", self._status_hits_for(self.weapon.mode)))

    def _load_base_stats(self) -> None:
        stats = dict(self.weapon.mode.stats)
        ammo = self.weapon.data.entry.ammo
        stats.update({
            "attack_speed": self.weapon.mode.stats.fire_rate,
            "magazine_capacity": ammo.get("magazine_size", 1),
            "reload_speed": ammo.get("reload_time", 0),
            "recharge_rate": ammo.get("recharge_rate", 0),
        })
        self.base = CalculatedStats(self.weapon.mode_stats_type(stats).with_defaults())

    def _resolve_build(self) -> None:
        evolutions = (
            Upgrade({f"{evolution} perk {perk}": {
                "type": "evolution",
                "max_rank": 0,
                "compatibility": {"types": []},
                "stats": self.weapon.data.entry.evolutions[evolution.removeprefix("evolution_")][str(perk)].get("stats", {}),
            }})
            for evolution, perk in self.weapon.evolutions.items()
        )
        self.build = Build(*self.weapon.build, *evolutions)
        entry = self.weapon.data.entry
        context = {
            "name": self.weapon.data.name,
            "type": entry.type,
            "subtype": entry.subtype,
            "trigger": self.weapon.mode.get("trigger"),
            "projectile": self.weapon.mode.get("delivery"),
            "aoe": self.weapon.mode.get("aoe", False),
        }
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
        self.modded = CalculatedStats()
        self.effective = CalculatedStats()
        self.average = AverageStats()
        self._resolve_build()
        self._load_base_stats()
        self._compute_modded_stats()
        self._compute_effective_stats()
        self._apply_condition_overload()
        self._compute_related_attacks()
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
