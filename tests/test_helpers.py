import unittest

from warframe_damage_calculator.calculators import helpers
from warframe_damage_calculator.fields.attack_result import AttackResult
from warframe_damage_calculator.fields.calculated import AverageStats
from warframe_damage_calculator.fields.weapon_data import Attack


class HelperTests(unittest.TestCase):
    def test_crit_multiplier(self):
        self.assertAlmostEqual(helpers.crit_multiplier(0.5, 3.0), 2.0)
        self.assertAlmostEqual(helpers.crit_multiplier(0.0, 3.0), 1.0)
        self.assertAlmostEqual(helpers.crit_multiplier(2.0, 2.0), 3.0)

    def test_refresh_dps_from_dph(self):
        average = AverageStats({
            "fire_rate": 2.0,
            "flat_dph": 100.0,
            "flat_weakpoint_dph": 200.0,
            "flat_dotph": 10.0,
            "flat_weakpoint_dotph": 20.0,
            "flat_dotps": 20.0,
            "flat_weakpoint_dotps": 40.0,
        })
        helpers.refresh_dps_from_dph(average)
        self.assertAlmostEqual(average.flat_dps, 200.0)
        self.assertAlmostEqual(average.flat_weakpoint_dps, 400.0)
        self.assertAlmostEqual(average.total_dph, 110.0)
        self.assertAlmostEqual(average.total_weakpoint_dph, 220.0)
        self.assertAlmostEqual(average.total_dps, 220.0)
        self.assertAlmostEqual(average.total_weakpoint_dps, 440.0)

    def test_flat_dotph_zero_when_no_damage(self):
        result = AttackResult({
            "name": "test",
            "attack": Attack({"name": "test", "stats": {"damage": {}}}),
        })
        self.assertEqual(helpers.flat_dotph(result), 0.0)

    def test_status_hits_uses_multishot(self):
        result = AttackResult({
            "name": "test",
            "attack": Attack({"name": "test", "stats": {"multishot": 1, "crit_chance": 0.1}}),
            "modded": {"multishot": 2.5, "multiplicative_crit_chance": 1, "flat_crit_chance": 0},
        })
        self.assertAlmostEqual(helpers.status_hits(result), 2.5)


if __name__ == "__main__":
    unittest.main()
