from __future__ import annotations

import unittest

from warframe_damage_calculator.mechanics import dist
from warframe_damage_calculator.upgrade_models import Upgrade


class UpgradeTests(unittest.TestCase):
    def test_upgrade_addition(self) -> None:
        left = Upgrade(damage_dist=dist(impact=0.5), base_damage=0.25, crit_chance=0.5, fire_rate_lock=True)
        right = Upgrade(damage_dist=dist(impact=0.1, slash=0.2), base_damage=0.75, crit_chance=0.25, fire_rate_lock=False, multishot_lock=True)
        combined = left + right

        self.assertAlmostEqual(combined.damage_dist.get("impact"), 0.6)
        self.assertAlmostEqual(combined.damage_dist.get("slash"), 0.2)
        self.assertAlmostEqual(combined.base_damage, 1.0)
        self.assertAlmostEqual(combined.crit_chance, 0.75)
        self.assertTrue(combined.fire_rate_lock)
        self.assertTrue(combined.multishot_lock)

    def test_upgrade_radd_supports_sum(self) -> None:
        upgrades = [Upgrade(base_damage=0.25), Upgrade(base_damage=0.75)]
        total = sum(upgrades)
        self.assertAlmostEqual(total.base_damage, 1.0)

    def test_upgrade_radd_non_zero_left_operand_raises(self) -> None:
        with self.assertRaises(TypeError):
            _ = 1 + Upgrade()


if __name__ == "__main__":
    unittest.main()
