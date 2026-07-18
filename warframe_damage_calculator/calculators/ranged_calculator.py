from collections.abc import Mapping
from typing import Any

from ..utils.functions import clamp, true_round
from ..models.data import Data
from ..models.dist import Dist
from .weapon_calculator import WeaponCalculator


class RangedCalculator(WeaponCalculator):
    DIST_FIELDS = WeaponCalculator.DIST_FIELDS | {"explosion_damage", "explosion_forced_procs"}
    DEFAULT_STATS = WeaponCalculator.DEFAULT_STATS | {"explosion_damage": Dist(), "explosion_forced_procs": Dist(), "multishot": 1.0, "fire_rate": 0.05, "burst_count": 1, "burst_delay": 0.0, "charge_time": 0.0, "reload_speed": 0.0, "recharge_rate": 0.0, "magazine_capacity": 1, "weakpoint_damage": 3.0, "explosion_total_damage": 0.0, "multiplicative_fire_rate": 1.0, "ammo_efficiency": 0.0, "multiplicative_weakpoint_crit_chance": 1.0, "weakpoint_crit_chance": 0.0, "internal_bleeding": 0.0}
    DEFAULT_BUILD = WeaponCalculator.DEFAULT_BUILD | {"weakpoint_damage": 0.0, "fire_rate_lock": False, "multiplicative_fire_rate": 0.0, "fire_rate": 0.0, "reload_speed": 0.0, "ammo_efficiency": 0.0, "magazine_capacity": 0.0, "multishot_lock": False, "multishot": 0.0, "multiplicative_weakpoint_crit_chance": 0.0, "weakpoint_crit_chance": 0.0, "internal_bleeding": 0.0}

    @classmethod
    def _base(cls, stats: Data | None = None) -> Data:
        values = super()._base(stats)
        values.explosion_total_damage = values.explosion_damage.total_damage()
        return values

    def _compute_moded_stats(self) -> None:
        super()._compute_moded_stats()
        build = self.weapon.build.stats.total
        self.moded.explosion_damage = self.moded.base_damage * self.base.explosion_damage.apply(build.damage).combine().sorted()
        self.moded.explosion_total_damage = self.moded.explosion_damage.total_damage()
        self.moded.weakpoint_damage = max(self.base.weakpoint_damage + build.weakpoint_damage, 1)
        self.moded.multiplicative_fire_rate = 1 if build.fire_rate_lock else max(1 + build.multiplicative_fire_rate, 1)
        self.moded.fire_rate = max(self.base.fire_rate * (1 if build.fire_rate_lock else (1 + build.fire_rate)), 0.05)
        self.moded.burst_count = max(self.base.burst_count, 1)
        self.moded.burst_delay = max(self.base.burst_delay, 0) / (1 if build.fire_rate_lock else max(1 + build.fire_rate, 1))
        self.moded.charge_time = max(self.base.charge_time, 0) / (1 if build.fire_rate_lock else max(1 + build.fire_rate, 0.01))
        self.moded.reload_speed = max(self.base.reload_speed, 0) / max(1 + build.reload_speed, 0.01)
        self.moded.recharge_rate = max(self.base.recharge_rate, 0)
        self.moded.ammo_efficiency = clamp(build.ammo_efficiency, 0, 1)
        self.moded.magazine_capacity = max(true_round(self.base.magazine_capacity * (1 + build.magazine_capacity)), 1)
        self.moded.multishot = max(self.base.multishot * (1 if build.multishot_lock else (1 + build.multishot)), 1)
        self.moded.multiplicative_weakpoint_crit_chance = max(1 + build.multiplicative_weakpoint_crit_chance, 1)
        self.moded.weakpoint_crit_chance = max(self.base.crit_chance * (1 + build.crit_chance + build.weakpoint_crit_chance), 0)
        self.moded.internal_bleeding = max(build.internal_bleeding * (2 if self.moded.fire_rate * self.moded.multiplicative_fire_rate < 2.5 else 1), 0)

    def _compute_effective_stats(self) -> None:
        super()._compute_effective_stats()
        self.effective.explosion_damage = self.moded.explosion_damage
        self.effective.explosion_total_damage = self.effective.explosion_damage.total_damage()
        self.effective.weakpoint_damage = self.moded.weakpoint_damage
        self.effective.fire_rate = self.moded.fire_rate * self.moded.multiplicative_fire_rate
        self.effective.burst_count = self.moded.burst_count
        self.effective.burst_delay = self.moded.burst_delay
        self.effective.charge_time = self.moded.charge_time / self.moded.multiplicative_fire_rate
        self.effective.reload_speed = self.moded.reload_speed + (0 if not self.weapon.data.context.get("is_battery", False) else float("inf") if self.moded.recharge_rate <= 0 else self.moded.magazine_capacity / self.moded.recharge_rate)
        self.effective.recharge_rate = self.moded.recharge_rate
        self.effective.ammo_efficiency = 1 - (1 - self.moded.ammo_efficiency) / (2 if self.weapon.data.context.get("is_beam", False) else 1)
        self.effective.magazine_capacity = self.moded.magazine_capacity
        self.effective.multishot = self.moded.multishot
        self.effective.weakpoint_crit_chance = self.moded.weakpoint_crit_chance * (self.moded.multiplicative_crit_chance + self.moded.multiplicative_weakpoint_crit_chance - 1) + self.moded.flat_crit_chance
        self.effective.internal_bleeding = self.moded.internal_bleeding

    def _compute_average_stats(self) -> None:
        super()._compute_average_stats()
        self.average.weakpoint_crit_chance = self.effective.weakpoint_crit_chance
        self.average.fire_rate = self._average_fire_rate()
        self.average.procs_per_shot = self.effective.status_chance * self.effective.multishot
        self.average.weakpoint_crit_multiplier = 1 + self.average.weakpoint_crit_chance * (self.effective.crit_damage - 1)
        self.average.beam_dot_multiplier = self.effective.multishot if self.weapon.data.context.get("is_beam", False) else 1
        self.average.flat_dph = (self.effective.total_damage * self.effective.multishot + self.effective.explosion_total_damage) * self.effective.faction_damage * self.average.crit_multiplier
        self.average.flat_weakpoint_dph = (self.effective.total_damage * self.effective.multishot * self.effective.weakpoint_damage * self.average.weakpoint_crit_multiplier + self.effective.explosion_total_damage * self.average.crit_multiplier) * self.effective.faction_damage
        self.average.flat_dps = self.average.fire_rate * self.average.flat_dph
        self.average.flat_weakpoint_dps = self.average.fire_rate * self.average.flat_weakpoint_dph
        self.average.flat_dotph = self._flat_dotph_for(self.effective.damage, self.base.forced_procs, self.average.crit_chance, self.average.crit_multiplier) + self._flat_dotph_for(self.effective.explosion_damage, self.base.explosion_forced_procs, self.average.crit_chance, self.average.crit_multiplier, include_multishot=False)
        self.average.flat_weakpoint_dotph = self._flat_dotph_for(self.effective.damage, self.base.forced_procs, self.average.weakpoint_crit_chance, self.average.weakpoint_crit_multiplier) + self._flat_dotph_for(self.effective.explosion_damage, self.base.explosion_forced_procs, self.average.crit_chance, self.average.crit_multiplier, include_multishot=False)
        self.average.flat_dotps = self.average.fire_rate * self.average.flat_dotph
        self.average.flat_weakpoint_dotps = self.average.fire_rate * self.average.flat_weakpoint_dotph
        self.average.total_dph = self.average.flat_dph + self.average.flat_dotph
        self.average.total_weakpoint_dph = self.average.flat_weakpoint_dph + self.average.flat_weakpoint_dotph
        self.average.total_dps = self.average.flat_dps + self.average.flat_dotps
        self.average.total_weakpoint_dps = self.average.flat_weakpoint_dps + self.average.flat_weakpoint_dotps

    def _average_fire_rate(self) -> float:
        cycle_time = self.effective.magazine_capacity / self.effective.burst_count * (self.effective.charge_time + (self.effective.burst_count - 1) * self.effective.burst_delay) + (self.effective.magazine_capacity / self.effective.burst_count - (1 - self.effective.ammo_efficiency)) / self.effective.fire_rate + (1 - self.effective.ammo_efficiency) * self.effective.reload_speed
        if cycle_time <= 0:
            return float("inf")
        return self.effective.magazine_capacity / cycle_time
