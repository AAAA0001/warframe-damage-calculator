from ..utils.constants import DOT_MULTIPLIERS
from ..utils.functions import clamp, true_round
from .weapon_calculator import WeaponCalculator


class MeleeCalculator(WeaponCalculator):
    DEFAULT_STATS = WeaponCalculator.DEFAULT_STATS | {"attack_speed": 1.0, "melee_doughty": 0.0, "melee_duplicate": 0.0}
    DEFAULT_BUILD = WeaponCalculator.DEFAULT_BUILD | {"attack_speed": 0.0, "melee_duplicate": 0.0, "melee_doughty": 0.0}

    def _compute_moded_stats(self) -> None:
        super()._compute_moded_stats()
        self.moded.attack_speed = max(self.base.attack_speed * (1 + self.weapon.build.results.total.attack_speed), 0)
        self.moded.melee_duplicate = clamp(self.weapon.build.results.total.melee_duplicate, 0, 1)
        self.moded.melee_doughty = clamp(self.weapon.build.results.total.melee_doughty, 0, 1)

    def _compute_effective_stats(self) -> None:
        super()._compute_effective_stats()
        self.effective.attack_speed = self.moded.attack_speed
        self.effective.melee_duplicate = self.moded.melee_duplicate
        self.effective.melee_doughty = self.moded.melee_doughty

    def _compute_average_stats(self) -> None:
        super()._compute_average_stats()
        self.average.melee_doughty_bonus = true_round(10 * self.effective.damage.weight("puncture") * self.effective.status_chance * self.effective.melee_doughty, 1)
        self.average.melee_duplicate_multiplier = 1 + self.effective.melee_duplicate * max(0, 1 - abs(self.effective.crit_chance - 1))
        self.average.flat_dph = self.effective.total_damage * self.effective.faction_damage * self.average.crit_multiplier * self.average.melee_duplicate_multiplier
        self.average.flat_dps = self.effective.attack_speed * self.average.flat_dph
        damage = self.effective.damage
        self.average.flat_dotph = sum(multiplier * damage.get(damage_type) * damage.weight(damage_type) for damage_type, multiplier in DOT_MULTIPLIERS) * self.effective.status_chance * self.effective.status_damage * self.effective.faction_damage ** 2 * self.average.crit_multiplier * self.average.melee_duplicate_multiplier
        self.average.flat_dotps = self.effective.attack_speed * self.average.flat_dotph
        self.average.total_dph = self.average.flat_dph + self.average.flat_dotph
        self.average.total_dps = self.average.flat_dps + self.average.flat_dotps
