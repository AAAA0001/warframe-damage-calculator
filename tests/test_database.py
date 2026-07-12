from __future__ import annotations

import json
import unittest
from pathlib import Path

from warframe_damage_calculator import Primary, Upgrade, arsenal
from warframe_damage_calculator.data import WarframeDatabase
from warframe_damage_calculator.models.dist import dist


DATABASE_DIR = (
    Path(__file__).resolve().parents[1]
    / "warframe_damage_calculator"
    / "data"
    / "database"
)


class WarframeDatabaseTests(unittest.TestCase):
    def test_weapon_uses_public_database_field_names(self) -> None:
        weapon = arsenal.get("Corinth Prime", type="primary")

        self.assertIsInstance(weapon, Primary)
        assert isinstance(weapon, Primary)
        self.assertEqual(weapon.stats.base.trigger, "semi")
        self.assertEqual(
            weapon.stats.base.damage_dist,
            dist({"impact": 25.2, "puncture": 37.8, "slash": 27.0}),
        )

    def test_upgrade_buckets_map_directly_to_upgrade_model(self) -> None:
        upgrade = arsenal.get("Galvanized Hell", type="mod")

        self.assertIsInstance(upgrade, Upgrade)
        assert isinstance(upgrade, Upgrade)
        self.assertEqual(upgrade.stats, {"multishot": 1.1})
        self.assertEqual(upgrade.stacking_stats, {"multishot": (0.3, "kill")})
        self.assertEqual(upgrade.max_stacks, 4)

    def test_rank_scaling_preserves_boolean_values(self) -> None:
        max_rank = arsenal.get("Critical Delay", type="mod")
        rank_zero = arsenal.get("Critical Delay", type="mod", rank=0)

        self.assertIsInstance(max_rank, Upgrade)
        self.assertIsInstance(rank_zero, Upgrade)
        assert isinstance(max_rank, Upgrade)
        assert isinstance(rank_zero, Upgrade)
        self.assertAlmostEqual(
            rank_zero.stats["crit_chance"],
            max_rank.stats["crit_chance"] / 6,
        )


    def test_rank_locked_stats_only_appear_at_the_required_rank(self) -> None:
        rank_four = arsenal.get("Primary Deadhead", type="arcane", rank=4)
        rank_five = arsenal.get("Primary Deadhead", type="arcane", rank=5)
        default_rank = arsenal.get("Primary Deadhead", type="arcane")

        self.assertIsInstance(rank_four, Upgrade)
        self.assertIsInstance(rank_five, Upgrade)
        self.assertIsInstance(default_rank, Upgrade)
        assert isinstance(rank_four, Upgrade)
        assert isinstance(rank_five, Upgrade)
        assert isinstance(default_rank, Upgrade)

        self.assertNotIn("weakpoint_damage", rank_four.stats)
        self.assertEqual(rank_five.stats["weakpoint_damage"], 0.3)
        self.assertEqual(default_rank.stats["weakpoint_damage"], 0.3)
        self.assertAlmostEqual(rank_four.stacking_stats["base_damage"][0], 1.0)
        self.assertEqual(rank_five.stacking_stats["base_damage"], (1.2, "headshot kill"))

    def test_rank_locked_stats_are_explicit_in_the_database(self) -> None:
        upgrades = json.loads((DATABASE_DIR / "upgrades.json").read_text(encoding="utf-8"))
        deadhead = upgrades["arcane"]["Primary Deadhead"]
        merciless = upgrades["arcane"]["Primary Merciless"]

        self.assertNotIn("weakpoint_damage", deadhead.get("stats", {}))
        self.assertEqual(deadhead["rank_locked_stats"], {"weakpoint_damage": [0.3, 5]})
        self.assertEqual(merciless["rank_locked_stats"], {"reload_speed": [0.3, 5]})

    def test_name_queries_do_not_require_object_construction(self) -> None:
        names = arsenal.get(type="semi", attribute="name")

        self.assertIsInstance(names, list)
        self.assertIn("Corinth Prime", names)
        self.assertIn("Semi-Shotgun Cannonade", names)

    def test_upgrade_stat_attributes_are_searchable(self) -> None:
        crit_values = arsenal.get(type="mod", attribute="crit_chance")

        self.assertIsInstance(crit_values, dict)
        self.assertEqual(crit_values["Critical Delay"], 2.0)

    def test_public_file_constructors(self) -> None:
        database = WarframeDatabase.from_folder(DATABASE_DIR)
        legacy_alias = WarframeDatabase._from_folder(DATABASE_DIR)

        self.assertIsInstance(database.get("Acceltra"), Primary)
        self.assertIsInstance(legacy_alias.get("Acceltra"), Primary)

    def test_database_uses_the_model_schema(self) -> None:
        weapons = json.loads((DATABASE_DIR / "weapons.json").read_text(encoding="utf-8"))
        upgrades = json.loads((DATABASE_DIR / "upgrades.json").read_text(encoding="utf-8"))

        self.assertEqual(set(weapons), {"primary", "secondary", "melee"})
        self.assertEqual(set(upgrades), {"mod", "arcane"})

        acceltra = weapons["primary"]["Acceltra"]
        self.assertIn("damage", acceltra)
        self.assertNotIn("damage_dist", acceltra)

        galvanized_hell = upgrades["mod"]["Galvanized Hell"]
        self.assertIn("stacking_stats", galvanized_hell)
        self.assertNotIn("stackables", galvanized_hell)
        self.assertNotIn("conditions", galvanized_hell)


if __name__ == "__main__":
    unittest.main()
