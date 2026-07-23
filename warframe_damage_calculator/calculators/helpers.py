from ..fields.calculated import AverageStats
from ..models.upgrade import Upgrade
from ..protocols import WeaponCalculatorOwner
from ..utils.types import Number


def crit_multiplier(crit_chance: Number, crit_damage: Number) -> float:
    return 1 + crit_chance * (crit_damage - 1)


def refresh_dps_from_dph(average: AverageStats) -> None:
    average.flat_dps = average.fire_rate * average.flat_dph
    average.flat_weakpoint_dps = average.fire_rate * average.flat_weakpoint_dph
    average.total_dph = average.flat_dph + average.flat_dotph
    average.total_weakpoint_dph = average.flat_weakpoint_dph + average.flat_weakpoint_dotph
    average.total_dps = average.flat_dps + average.flat_dotps
    average.total_weakpoint_dps = average.flat_weakpoint_dps + average.flat_weakpoint_dotps


def selected_evolution_upgrades(weapon: WeaponCalculatorOwner) -> list[Upgrade]:
    return [Upgrade({"name": f"evolution {tier} perk {perk}", "type": "evolution", "stats": weapon.data.evolutions[str(tier)][str(perk)].get("stats", {})}) for tier, perk in weapon._evolutions.items()]
