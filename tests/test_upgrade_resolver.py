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

    def test_upgrade_copy_is_independent(self) -> None:
        original = Upgrade(stats={"base_damage": 1}, conditional_stats={"crit_chance": [0.5, "headshot"]}, stacking_stats={"multishot": [0.2, "kill"]}, rank_locked_stats={"status_chance": [0.3, 2]}, context={"max_rank": 5, "requirements": {"trigger": ["semi"]}})
        copied = original.copy()
        copied.stats["base_damage"] = 2
        for bucket in (copied.conditional_stats, copied.stacking_stats, copied.rank_locked_stats): next(iter(bucket.values()))[0] = 1
        copied.context["requirements"]["trigger"].append("auto")
        self.assertEqual((original.stats["base_damage"], original.conditional_stats["crit_chance"][0], original.stacking_stats["multishot"][0], original.rank_locked_stats["status_chance"][0]), (1, 0.5, 0.2, 0.3))
        self.assertEqual(original.context["requirements"], {"trigger": ["semi"]})
        self.assertEqual(original.copy(stats={"base_damage": 3}).stats["base_damage"], 3)

    def test_upgrade_validation(self) -> None:
        cases = (({"conditional_stats": {"base_damage": 1}}, r"expected \(value, condition\)"), ({"conditional_stats": {"base_damage": [1, ""]}}, "non-empty condition"), ({"stacking_stats": {"base_damage": 1}}, r"expected \(value, condition\)"), ({"rank_locked_stats": {"base_damage": [1, "five"]}}, "required_rank"), ({"context": {"max_rank": 5}, "rank_locked_stats": {"base_damage": [1, 6]}}, "exceeds max_rank"))
        for kwargs, message in cases:
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex((TypeError, ValueError), message): Upgrade(**kwargs)
        for context in ({"max_rank": True}, {"max_rank": 5, "rank": True}, {"max_stacks": True}, {"max_stacks": 5, "stacks": True}, {"max_rank": 5, "rank": 6}, {"max_stacks": 3, "stacks": 10}):
            with self.subTest(context=context), self.assertRaises((TypeError, ValueError)): Upgrade(context=context)
        for stats, message in (({"base_damage": True}, "int or float"), ({"multishot_lock": 1}, "bool")):
            with self.subTest(stats=stats), self.assertRaisesRegex(TypeError, message): Upgrade(stats=stats)
        self.assertEqual(Upgrade(conditional_stats={"base_damage": (1, "active")}).conditional_stats["base_damage"], [1, "active"])
        self.assertEqual(Upgrade(stats={"damage": {"impact": 0.5}}).stats["damage"], dist(impact=0.5))


if __name__ == "__main__":
    unittest.main()
