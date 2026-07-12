from warframe_damage_calculator import Build, Primary, Upgrade, arsenal


def main() -> None:
    weapon = arsenal.get("Corinth Prime", type="primary")
    upgrades = [
        Upgrade(
            name="Riven",
            stats={
                "impact": -0.886,
                "crit_damage": 0.855,
                "multishot": 1.126,
                "crit_chance": 0.887,
            },
        ),
        arsenal.get("Galvanized Hell", type="mod"),
        arsenal.get("Semi-Shotgun Cannonade", type="mod"),
        arsenal.get("Hunter Munitions", type="mod"),
        arsenal.get("Primed Chilling Grasp", type="mod"),
        arsenal.get("Primed Ravage", type="mod"),
        arsenal.get("Critical Delay", type="mod"),
        arsenal.get("Toxic Barrage", type="mod"),
        arsenal.get("Vigilante Supplies", type="mod"),
        arsenal.get("Primary Merciless", type="arcane"),
        Upgrade(name="Buff", stats={"flat_crit_damage": 1.2}),
    ]

    assert isinstance(weapon, Primary)
    assert all(isinstance(upgrade, Upgrade) for upgrade in upgrades)

    weapon.configure(Build(*upgrades))
    print(weapon.format.upgrades())


if __name__ == "__main__":
    main()
