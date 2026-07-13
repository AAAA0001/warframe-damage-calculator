from __future__ import annotations

import unittest
from dataclasses import is_dataclass

from warframe_damage_calculator import Build, Primary, Upgrade, arsenal
from warframe_damage_calculator.calculators import UpgradeResolver
from warframe_damage_calculator.models.dist import dist


class UpgradeResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.weapon = arsenal.get("Braton")
        self.assertIsInstance(self.weapon, Primary)

    def resolve(self) -> Build:
        return UpgradeResolver(self.weapon.context).resolve(self.weapon.build)

    def test_upgrade_is_a_normal_class(self) -> None:
        self.assertFalse(is_dataclass(Upgrade))

    def test_resolve_returns_build_and_merges_damage_types(self) -> None:
        build = Build(Upgrade(stats={"impact": 0.5}), Upgrade(stats={"heat": 0.25}))
        resolver = UpgradeResolver(self.weapon.context)
        resolved = resolver.resolve(build)
        self.assertIs(resolver.weapon_context, self.weapon.context)
        self.assertIsInstance(resolved, Build)
        self.assertEqual(resolved.get("damage"), dist(impact=0.5, heat=0.25))

    def test_rank_defaults_to_max_and_scales_from_context(self) -> None:
        maximum = arsenal.get("Critical Delay")
        rank_zero = arsenal.get("Critical Delay", context={"rank": 0})
        self.assertIsInstance(maximum, Upgrade)
        self.assertIsInstance(rank_zero, Upgrade)
        self.weapon.configure(maximum)
        maximum_value = self.resolve().get("crit_chance")
        self.weapon.configure(rank_zero)
        self.assertAlmostEqual(self.resolve().get("crit_chance"), maximum_value / (maximum.context["max_rank"] + 1))

    def test_conditions_and_stacks_default_to_active_and_max(self) -> None:
        upgrade = Upgrade(context={"max_stacks": 3}, conditional_stats={"base_damage": [1, "active"]}, stacking_stats={"crit_chance": [0.2, "stacks"]})
        self.weapon.configure(upgrade)
        resolved = self.resolve()
        self.assertEqual(resolved.get("base_damage"), 1)
        self.assertAlmostEqual(resolved.get("crit_chance"), 0.6)

    def test_explicit_context_disables_omitted_conditions(self) -> None:
        upgrade = Upgrade(context={"max_stacks": 3, "active": False, "stacks": 1}, conditional_stats={"base_damage": [1, "active"]}, stacking_stats={"crit_chance": [0.2, "stacks"]})
        self.weapon.configure(upgrade)
        resolved = self.resolve()
        self.assertEqual(resolved.get("base_damage"), 0)
        self.assertEqual(resolved.get("crit_chance"), 0.2)

    def test_stack_count_is_capped(self) -> None:
        upgrade = Upgrade(context={"max_stacks": 3, "stacks": 10}, stacking_stats={"base_damage": [0.5, "stacks"]})
        self.weapon.configure(upgrade)
        self.assertEqual(self.resolve().get("base_damage"), 1.5)


if __name__ == "__main__":
    unittest.main()
