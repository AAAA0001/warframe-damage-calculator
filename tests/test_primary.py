from __future__ import annotations

import unittest

from warframe_damage_calculator import Primary, Upgrade, arsenal
from warframe_damage_calculator.calculators import UpgradeResolver


class PrimaryTests(unittest.TestCase):
    def test_all_primary_weapons_construct_and_calculate(self) -> None:
        for name in arsenal.weapons["primary"]:
            with self.subTest(name=name):
                weapon = arsenal.get(name)
                self.assertIsInstance(weapon, Primary)
                weapon.stats.total_dps

    def test_primary_blight_uses_toxin_stacks(self) -> None:
        weapon = arsenal.get("Braton")
        blight = arsenal.get("Primary Blight", context={"toxin proc": 5})
        self.assertIsInstance(weapon, Primary)
        self.assertIsInstance(blight, Upgrade)
        weapon.configure(blight)
        resolved = UpgradeResolver(weapon.context).resolve(weapon.build)
        self.assertAlmostEqual(resolved.get("crit_damage"), 0.18)
        self.assertAlmostEqual(resolved.get("multishot"), 0.09)

    def test_configure_contextualizes_without_mutating_the_original_upgrade(self) -> None:
        weapon = arsenal.get("Braton")
        upgrade = Upgrade(context={"headshot": True})
        self.assertIsInstance(weapon, Primary)
        weapon.configure(upgrade)
        self.assertTrue(upgrade.context["headshot"])
        self.assertNotIn("sacrificial set", upgrade.context)
        self.assertTrue(weapon.build.upgrades[0].context["headshot"])
        self.assertFalse(weapon.build.upgrades[0].context["sacrificial set"])

    def test_weapon_context_accepts_custom_shared_conditions(self) -> None:
        weapon = Primary(stats={"damage": {"impact": 10}}, context={"type": "rifle", "buff": True})
        upgrade = Upgrade(conditional_stats={"base_damage": [1, "buff"]})
        self.assertEqual(weapon.context, {"category": "primary", "type": "rifle", "buff": True})
        weapon.configure(upgrade)
        self.assertEqual(weapon.stats.build.get("base_damage"), 1)
        self.assertEqual(weapon.stats.moded["base_damage"], 2)

    def test_constructor_only_accepts_stats_and_context(self) -> None:
        with self.assertRaises(TypeError):
            Primary(damage={"impact": 10})

    def test_upgrade_formatter_uses_the_weapon_build(self) -> None:
        weapon = arsenal.get("Braton")
        serration = arsenal.get("Serration")
        critical_delay = arsenal.get("Critical Delay")
        self.assertIsInstance(weapon, Primary)
        self.assertIsInstance(serration, Upgrade)
        self.assertIsInstance(critical_delay, Upgrade)
        weapon.configure(serration, critical_delay)
        damage = weapon.stats.total_dps
        output = weapon.format.upgrades()
        self.assertIn("Serration:", output)
        self.assertIn("Critical Delay:", output)
        self.assertEqual(weapon.stats.total_dps, damage)

    def test_empty_upgrade_formatter(self) -> None:
        self.assertEqual(Primary().format.upgrades(), "")


if __name__ == "__main__":
    unittest.main()
