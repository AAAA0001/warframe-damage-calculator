from ..utils.functions import clamp, true_round
from .weapon_calculator import WeaponCalculator


class RangedCalculator(WeaponCalculator):
    def _compute_modded_stats(self) -> None:
        super()._compute_modded_stats()
        build = self.build.stats.total
        
        self.modded.weakpoint_damage = max(self.base.weakpoint_damage + build.weakpoint_damage, 1)
        self.modded.multiplicative_fire_rate = 1 if build.fire_rate_lock else max(1 + build.multiplicative_fire_rate, 1)
        self.modded.fire_rate = max(self.base.fire_rate * (1 if build.fire_rate_lock else (1 + build.fire_rate)), 0.05)
        self.modded.burst_count = max(self.base.burst_count, 1)
        self.modded.burst_delay = max(self.base.burst_delay, 0) / (1 if build.fire_rate_lock else max(1 + build.fire_rate, 1))
        self.modded.charge_time = max(self.base.charge_time, 0) / (1 if build.fire_rate_lock else max(1 + build.fire_rate, 0.01))
        self.modded.reload_speed = max(self.base.reload_speed, 0) / max(1 + build.reload_speed, 0.01)
        self.modded.recharge_rate = max(self.base.recharge_rate, 0)
        self.modded.ammo_efficiency = clamp(build.ammo_efficiency, 0, 1)
        self.modded.magazine_capacity = max(true_round(self.base.magazine_capacity * (1 + build.magazine_capacity)), 1)
        self.modded.multishot = max(self.base.multishot * (1 if build.multishot_lock else (1 + build.multishot)), 1)
        self.modded.multiplicative_weakpoint_crit_chance = max(1 + build.multiplicative_weakpoint_crit_chance, 1)
        self.modded.weakpoint_crit_chance = max(self.base.crit_chance * (1 + build.crit_chance + build.weakpoint_crit_chance), 0)
        self.modded.internal_bleeding = max(build.internal_bleeding * (2 if self.modded.fire_rate * self.modded.multiplicative_fire_rate < 2.5 else 1), 0)

    def _compute_effective_stats(self) -> None:
        super()._compute_effective_stats()
        is_battery = "recharge_delay" in self.weapon.data.entry.ammo
        is_beam = any(attack.get("delivery") == "beam" for attack in self.weapon.data.entry.attacks.values())

        self.effective.weakpoint_damage = self.modded.weakpoint_damage
        self.effective.fire_rate = self.modded.fire_rate * self.modded.multiplicative_fire_rate
        self.effective.burst_count = self.modded.burst_count
        self.effective.burst_delay = self.modded.burst_delay
        self.effective.charge_time = self.modded.charge_time / self.modded.multiplicative_fire_rate
        self.effective.reload_speed = self.modded.reload_speed + (0 if not is_battery else float("inf") if self.modded.recharge_rate <= 0 else self.modded.magazine_capacity / self.modded.recharge_rate)
        self.effective.recharge_rate = self.modded.recharge_rate
        self.effective.ammo_efficiency = 1 - (1 - self.modded.ammo_efficiency) / (2 if is_beam else 1)
        self.effective.magazine_capacity = self.modded.magazine_capacity
        self.effective.multishot = self.modded.multishot
        self.effective.weakpoint_crit_chance = self.modded.weakpoint_crit_chance * (self.modded.multiplicative_crit_chance + self.modded.multiplicative_weakpoint_crit_chance - 1) + self.modded.flat_crit_chance
        self.effective.internal_bleeding = self.modded.internal_bleeding

    def _compute_average_stats(self) -> None:
        super()._compute_average_stats()
        is_beam = any(attack.get("delivery") == "beam" for attack in self.weapon.data.entry.attacks.values())
        related_flat = sum(state.damage.total_damage() * state.multishot * state.faction_damage * (1 + state.crit_chance * (state.crit_damage - 1)) for state in self.related.values())
        related_weakpoint = sum(state.damage.total_damage() * state.multishot * state.faction_damage * state.weakpoint_damage * (1 + state.weakpoint_crit_chance * (state.crit_damage - 1)) for state in self.related.values())
        related_dot = self._related_dotph()

        self.average.weakpoint_crit_chance = self.effective.weakpoint_crit_chance
        self.average.fire_rate = self._attacks_per_second_for(self.weapon.mode)
        self.average.procs_per_shot = self.effective.status_chance * self.effective.multishot
        self.average.weakpoint_crit_multiplier = 1 + self.average.weakpoint_crit_chance * (self.effective.crit_damage - 1)
        self.average.beam_dot_multiplier = self.effective.multishot if is_beam else 1
        self.average.flat_dph = self.effective.damage.total_damage() * self.effective.multishot * self.effective.faction_damage * self.average.crit_multiplier + related_flat
        self.average.flat_weakpoint_dph = self.effective.damage.total_damage() * self.effective.multishot * self.effective.weakpoint_damage * self.average.weakpoint_crit_multiplier * self.effective.faction_damage + related_weakpoint
        self.average.flat_dps = self.average.fire_rate * self.average.flat_dph
        self.average.flat_weakpoint_dps = self.average.fire_rate * self.average.flat_weakpoint_dph
        self.average.flat_dotph = self._flat_dotph_for(self.effective.damage, self.base.forced_procs, self.average.crit_chance, self.average.crit_multiplier) + related_dot
        self.average.flat_weakpoint_dotph = self._flat_dotph_for(self.effective.damage, self.base.forced_procs, self.average.weakpoint_crit_chance, self.average.weakpoint_crit_multiplier) + related_dot
        self.average.flat_dotps = self.average.fire_rate * self.average.flat_dotph
        self.average.flat_weakpoint_dotps = self.average.fire_rate * self.average.flat_weakpoint_dotph
        self.average.total_dph = self.average.flat_dph + self.average.flat_dotph
        self.average.total_weakpoint_dph = self.average.flat_weakpoint_dph + self.average.flat_weakpoint_dotph
        self.average.total_dps = self.average.flat_dps + self.average.flat_dotps
        self.average.total_weakpoint_dps = self.average.flat_weakpoint_dps + self.average.flat_weakpoint_dotps
