# Warframe Damage Calculator

> Deterministic Warframe weapon damage calculations using expected-value
> formulas.

**Warframe Damage Calculator** is a Python library for modeling Warframe
weapon performance using deterministic mathematics rather than Monte
Carlo simulation. Instead of simulating thousands of shots, the library
computes the statistical average outcome of every attack, making it
suitable for build optimization, theorycrafting, and external tooling.

The project is built around a simple object-oriented API with reusable
weapon definitions, upgrades, and builds.

------------------------------------------------------------------------

## Features

-   Deterministic expected-value calculations
-   Primary, Secondary, and Melee weapon support
-   Beam, battery, burst-fire, and charge weapon support
-   Physical, elemental, and combined elemental damage
-   Critical and status systems
-   Hunter Munitions, Hemorrhage, Secondary Enervate, Secondary
    Encumber, Melee Duplicate, Melee Doughty, Primed Chamber, and
    Vigilante support
-   Flat and damage-over-time calculations
-   Small, Pythonic public API

------------------------------------------------------------------------

## Requirements

-   Python **3.12+**

------------------------------------------------------------------------

## Installation

``` bash
pip install git+https://github.com/AAAA0001/warframe-damage-calculator.git
```

Development install:

``` bash
git clone https://github.com/AAAA0001/warframe-damage-calculator.git
cd warframe-damage-calculator
pip install -e .
```

------------------------------------------------------------------------

## Quick Start

``` python
from warframe_damage_calculator import Build, arsenal

weapon = arsenal.get("Corinth Prime")
multishot = arsenal.get("Galvanized Hell")
cold = arsenal.get("Primed Chilling Grasp")

multishot.context.kill = 4
cold.context.rank = 3
weapon.configure(Build(multishot, cold))
print(weapon.format.summary())
```

For more complete examples, see the `examples/` directory.

------------------------------------------------------------------------

## Database Loader

The bundled database uses the same names as the public model constructors. The
main entry point is `arsenal.get()`:

```python
weapon = arsenal.get("Acceltra Prime")
mod = arsenal.get("Critical Delay", context={"rank": 5})
shotgun_names = arsenal.get(type="shotgun", attribute="name")
crit_values = arsenal.get(type="mod", attribute="crit_chance")
```

Named lookups return the single matching weapon or upgrade without requiring `type`. When `name` is omitted, `get()` returns all matching items. Passing
`attribute="name"` returns only their names without constructing every model.
Filters accept broad categories such as `weapon`, `upgrade`, `primary`, `mod`,
and `arcane`, as well as weapon types and triggers such as `shotgun`, `bow`, or
`semi`.

The JSON schema mirrors the model API:

- Weapon sections: `primary`, `secondary`, and `melee`.
- Upgrade sections: `mod` and `arcane`.
- Weapon damage fields: `damage` and `explosion_damage`.
- Upgrade buckets: `stats`, `conditional_stats`, and `stacking_stats`.
- Conditional entries are stored as `[value, condition]`.

------------------------------------------------------------------------

## Design

Every weapon follows the same pipeline:

``` text
Base weapon
      │
      ▼
Build (mods, arcanes, buffs)
      │
      ▼
Derived statistics
      │
      ▼
Damage calculations
      │
      ▼
Formatted output
```

The library separates responsibilities into models, calculators, and
formatters so the same weapon definition can be reused with different
builds.

------------------------------------------------------------------------

## Public API

``` python
from warframe_damage_calculator import (
    Record,
    Upgrade,
    Build,
    Primary,
    Secondary,
    Melee,
)
```

 | Object      | Description                               |
 |-------------|-------------------------------------------|
 |`Record`     | Keyword-initialized named values.          |
 |`Upgrade`    | A single modifier (mod, arcane, or buff). |
 |`Build`      | A collection of upgrades.                 |
 |`Primary`    | Primary weapon model.                     |
 |`Secondary`  | Secondary weapon model.                   |
 |`Melee`      | Melee weapon model.                       |

Typical workflow:

1.  Create a weapon.
2.  Create one or more `Upgrade` objects.
3.  Combine them into a `Build` (optional).
4.  Apply the build with `weapon.configure(build)` or `weapon.configure(upgrade_1, upgrade_2, ...)`.
5.  Read values from `weapon.stats`.
6.  Print results with `weapon.format.summary()`.

Since `configure()` returns the weapon, the following is also valid:

``` python
weapon = Primary(...).configure(build)
```

Weapon stats and context use `Record`, which is initialized with keyword
arguments and exposes values through attributes. The optimized distribution
object is an internal calculator detail:

```python
weapon = Primary(
    stats=Record(
        damage={"impact": 20, "puncture": 30, "slash": 50},
        forced_procs={"slash": 1},
        explosion_damage={"heat": 100},
        explosion_forced_procs={"heat": 1},
    ),
    context=Record(type="rifle"),
)
```

------------------------------------------------------------------------

## Upgrade Fields

Upgrades store modifiers in `Record` objects. Conditional and stacking entries use
a two-item `[value, condition]` sequence:

```python
upgrade = Upgrade(
    context=Record(name="Example Arcane", max_stacks=3),
    stats=Record(reload_speed=0.3),
    conditional_stats=Record(crit_chance=[0.5, "headshot"]),
    stacking_stats=Record(base_damage=[0.3, "kill"]),
)
```

Descriptive metadata is stored only in `context`. Upgrade contexts include
`name`, `category`, `compatibility`, `incompatibility`, `requirements`,
`max_rank`, `max_stacks`, and `is_exilus`; weapon contexts include `name`,
`category`, `type`, and ranged trigger/beam/battery metadata when applicable.
Runtime conditions remain in the same record.

Weapon calculations use `Record` objects for the `base`, `moded`, and `effective` stat buckets.
Read calculated values through attributes, for example,
`weapon.stats.effective.crit_chance`.

Weapon and build conditions such as `bow` and `sacrificial set` resolve
automatically. Combat conditions and stack counts are stored on each upgrade:

```python
upgrade.context.headshot = True
upgrade.context.kill = 3
weapon.configure(build)
```

The resolver supplies weapon and build context separately while resolving, so
automatic conditions never become persistent upgrade context. When an upgrade
has no manual condition context, its conditional stats default to active and
its stacking stats use `max_stacks`. Once manual condition context is supplied,
omitted manual conditions are inactive and omitted stack counts are zero.
Rank-locked stats use `upgrade.context.rank`; it defaults to `max_rank`, or
zero when the upgrade has no maximum rank.

The `Upgrade` and `Build` models only store data. Condition matching, stack
limits, and bucket merging are handled by `UpgradeResolver`.

`Build.contextualize()` applies shared context to every upgrade. Pass `copy=True` to return an independent contextualized build:

```python
build.contextualize({"kill": 3})
contextualized = build.contextualize(weapon.context, copy=True)
```

### Damage

-   `damage`
-   `base_damage`
-   `multiplicative_base_damage`
-   `faction_damage`
-   `weakpoint_damage`
-   `multishot`

### Fire Control

-   `attack_speed`
-   `fire_rate`
-   `multiplicative_fire_rate`
-   `burst_count`
-   `bust_delay`
-   `charge_time`
-   `reload_speed`
-   `recharge_rate`
-   `ammo_efficiency`
-   `magazine_capacity`
-   `is_beam`
-   `is_battery`

### Critical

-   `crit_chance`
-   `flat_crit_chance`
-   `multiplicative_crit_chance`
-   `weakpoint_crit_chance`
-   `multiplicative_weakpoint_crit_chance`
-   `crit_damage`
-   `flat_crit_damage`

### Status

-   `forced_procs`
-   `status_chance`
-   `status_damage`

### Special Effects

-   `hunter_munitions`
-   `internal_bleeding`
-   `primed_chamber`
-   `vigilante_bonus`
-   `secondary_enervate`
-   `secondary_encumber`
-   `melee_duplicate`
-   `melee_doughty`

------------------------------------------------------------------------

## Supported Features

### Weapons

- [x] Primary weapons
- [x] Secondary weapons
- [x] Melee light attacks
- [x] Beam weapons
- [x] Hitscan weapons
- [x] Charge weapons
- [x] Battery weapons
- [x] Burst-fire weapons
- [ ] Melee heavy attacks
- [ ] Melee slam attacks
- [ ] Projectile falloff

### Damage

- [x] Physical damage
- [x] Elemental damage
- [x] Combined elements
- [x] Damage weighting
- [x] Base, multiplicative, faction, and weakpoint damage
- [x] Critical calculations
- [ ] Enemy defenses and damage attenuation

### Status

- [x] Expected status procs
- [x] DoT status effects
- [x] Forced procs
- [x] Hunter Munitions
- [x] Internal Bleeding / Hemorrhage
- [x] Secondary Encumber
- [ ] Non-DoT status effects

### Calculations

- [x] Flat DPH / DPS
- [x] DoT DPH / DPS
- [x] Total DPH / DPS
- [x] Effective fire rate
- [x] Expected status procs per shot
- [ ] Time-to-kill
- [ ] Damage contribution breakdowns

------------------------------------------------------------------------

## Assumptions

The library computes **expected values** rather than simulating
individual shots. Results therefore represent the statistical long-term
average and may not exactly match any single shot fired in-game.

### Damage

-   Explosive damage does **not** benefit from **multiplicative base
    damage**.
-   If **Hunter Munitions** and **Internal Bleeding (Hemorrhage)**
    trigger simultaneously, only the higher-damage Slash proc is
    counted. *(Wiki)*

### Secondary Encumber

-   Secondary Encumber scales with total damage, status damage, faction
    damage, and critical damage.
-   Secondary Encumber can trigger Hemorrhage.
-   Secondary Encumber can trigger at most once per shot. *(Wiki)*

### Fire Cycle

-   Burst delay is affected by positive fire rate.
-   Burst delay is not reduced by negative fire rate. *(Wiki)*
-   Charge time scales with fire rate. *(Wiki)*
-   Recharge rate is independent of reload speed. *(Wiki)*
-   Beam weapons consume **0.5 ammo per tick**. *(Wiki)*
-   The weapon firing cycle is modeled as follows.

``` text
[ammo cost] ← (1 - [ammo efficiency]) ÷ (IF [is beam] THEN 2 ELSE 1)
[effective reload time] ← [reload time] + (IF [is battery] THEN [magazine capacity] / [recharge rate] ELSE 0)
[magazine] ← [magazine capacity]

REPEAT
    WAIT [charge time] seconds
    [primed chamber is active] ← ⌈[magazine]⌉ = [magazine capacity]

    SHOOT 1 round
    [magazine] ← [magazine] - [ammo cost]

    REPEAT [burst count] - 1 TIMES
        WAIT [burst delay] seconds
        [primed chamber is active] ← ⌈[magazine]⌉ = [magazine capacity]

        SHOOT 1 round
        [magazine] ← [magazine] - [ammo cost]

        IF [magazine] ≤ 0 THEN
            BREAK
    END REPEAT

    IF [magazine] ≤ 0 THEN
        WAIT [effective reload time] seconds
        [magazine] ← [magazine capacity]
    ELSE
        WAIT 1 ÷ [fire rate] seconds
    END IF
END REPEAT
```

------------------------------------------------------------------------

## Contributing

Bug reports, feature requests, and pull requests are welcome.

## License

Released under the MIT License.
