from __future__ import annotations

import unittest

from warframe_damage_calculator import Build, Upgrade


class BuildTests(unittest.TestCase):
    def test_add_and_remove_upgrades(self) -> None:
        first = Upgrade(context={"name": "First"})
        second = Upgrade(context={"name": "Second"})
        self.assertEqual((Build(first) + second).upgrades, [first, second])
        self.assertEqual((Build(first, second) - first).upgrades, [second])

    def test_get_aggregates_numeric_stats(self) -> None:
        build = Build(Upgrade(stats={"base_damage": 1}), Upgrade(stats={"base_damage": 2}))
        self.assertEqual(build.get("base_damage"), 3)
        self.assertEqual(build.get("crit_chance"), 0)

    def test_boolean_stats_merge_with_or(self) -> None:
        build = Build(Upgrade(stats={"fire_rate_lock": False}), Upgrade(stats={"fire_rate_lock": True}))
        self.assertIs(build.get("fire_rate_lock"), True)

    def test_boolean_stats_reject_numbers(self) -> None:
        with self.assertRaisesRegex(TypeError, "expected bool"):
            Upgrade(stats={"fire_rate_lock": 1})

    def test_only_upgrades_are_accepted(self) -> None:
        with self.assertRaisesRegex(TypeError, "Build only accepts Upgrade objects"):
            Build(object())

    def test_contextualize_updates_the_build_by_default(self) -> None:
        build = Build(Upgrade())
        self.assertIs(build.contextualize({"kill": 3}), build)
        self.assertEqual(build.upgrades[0].context["kill"], 3)

    def test_contextualize_can_return_an_independent_build(self) -> None:
        upgrade = Upgrade(stats={"base_damage": 1}, context={"name": "Example", "rank": 2, "requirements": {"trigger": ["semi"]}})
        original = Build(upgrade)
        contextualized = original.contextualize({"primary": True, "weapon": "rifle"}, copy=True)
        self.assertIsNot(contextualized, original)
        self.assertIsNot(contextualized.upgrades[0], upgrade)
        self.assertEqual({key: contextualized.upgrades[0].context[key] for key in ("rank", "primary", "weapon")}, {"rank": 2, "primary": True, "weapon": "rifle"})
        self.assertEqual(upgrade.context["rank"], 2)
        self.assertEqual(upgrade.context["name"], "Example")
        contextualized.upgrades[0].stats["base_damage"] = 2
        contextualized.upgrades[0].context["requirements"]["trigger"].append("auto")
        self.assertEqual((upgrade.stats["base_damage"], upgrade.context["requirements"]), (1, {"trigger": ["semi"]}))

if __name__ == "__main__":
    unittest.main()
