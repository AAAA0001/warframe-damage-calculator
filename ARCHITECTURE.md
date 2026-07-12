# Architecture

## Class Inheritance

```text
Build
└── Upgrade

Weapon
├── Ranged
│   ├── Primary
│   └── Secondary
└── Melee

WeaponState
├── RangedState
│   ├── PrimaryState
│   └── SecondaryState
└── MeleeState

TypedDict
├── WeaponFields
│   ├── RangedFields
│   │   ├── PrimaryFields
│   │   └── SecondaryFields
│   └── MeleeFields
└── DamageFields

WeaponCalculator
├── RangedCalculator
│   ├── PrimaryCalculator
│   └── SecondaryCalculator
└── MeleeCalculator

WeaponFormatter
├── RangedFormatter
│   ├── PrimaryFormatter
│   └── SecondaryFormatter
└── MeleeFormatter
```

## Class Ownership

```text
Weapon
│
├─ owns ─► WeaponCalculator
│          │
│          ├─ owns ─► WeaponState (base)
│          ├─ owns ─► WeaponState (modded)
│          ├─ owns ─► WeaponState (effective)
│          └─ owns ─► Build
│                     │
│                     └─ owns ─► Upgrade
│                                │
│                                └─ owns ─► dist
│
└─ owns ─► WeaponFormatter
           │
           └─ references ─► WeaponCalculator

Melee
│
├─ owns ─► MeleeCalculator
│          │
│          ├─ owns ─► MeleeState (base)
│          ├─ owns ─► MeleeState (modded)
│          ├─ owns ─► MeleeState (effective)
│          └─ owns ─► Build
│                     │
│                     └─ owns ─► Upgrade
│                                │
│                                └─ owns ─► dist
│
└─ owns ─► MeleeFormatter
           │
           └─ references ─► MeleeCalculator

Ranged
│
├─ owns ─► RangedCalculator
│          │
│          ├─ owns ─► RangedState (base)
│          ├─ owns ─► RangedState (modded)
│          ├─ owns ─► RangedState (effective)
│          └─ owns ─► Build
│                     │
│                     └─ owns ─► Upgrade
│                                │
│                                └─ owns ─► dist
│
└─ owns ─► RangedFormatter
           │
           └─ references ─► RangedCalculator

Primary
│
├─ owns ─► PrimaryCalculator
│          │
│          ├─ owns ─► PrimaryState (base)
│          ├─ owns ─► PrimaryState (modded)
│          ├─ owns ─► PrimaryState (effective)
│          └─ owns ─► Build
│                     │
│                     └─ owns ─► Upgrade
│                                │
│                                └─ owns ─► dist
│
└─ owns ─► PrimaryFormatter
           │
           └─ references ─► PrimaryCalculator

Secondary
│
├─ owns ─► SecondaryCalculator
│          │
│          ├─ owns ─► SecondaryState (base)
│          ├─ owns ─► SecondaryState (modded)
│          ├─ owns ─► SecondaryState (effective)
│          └─ owns ─► Build
│                     │
│                     └─ owns ─► Upgrade
│                                │
│                                └─ owns ─► dist
│
└─ owns ─► SecondaryFormatter
           │
           └─ references ─► SecondaryCalculator
```

## Package Architecture

```text
warframe_damage_calculator/
│
├── __init__.py
│
├── data/
│   │
│   ├── loader.py          # Public database access
│   ├── construction.py    # Model factory
│   ├── matching.py        # Category/type filtering
│   ├── normalization.py   # Name normalization
│   ├── schema.py          # Database record types
│   ├── paths.py           # JSON loading and paths
│   └── database/
│       ├── weapons.json
│       └── upgrades.json
│
├── models/
│   │
│   ├── dist.py
│   ├── upgrade.py
│   ├── build.py
│   │
│   ├── weapon.py
│   ├── ranged.py
│   ├── primary.py
│   ├── secondary.py
│   └── melee.py
│
├── states/
│   │
│   ├── weapon_state.py
│   ├── ranged_state.py
│   ├── primary_state.py
│   ├── secondary_state.py
│   └── melee_state.py
│
├── fields/
│   │
│   ├── weapon_fields.py
│   ├── ranged_fields.py
│   ├── damage_fields.py
│   ├── primary_fields.py
│   ├── secondary_fields.py
│   └── melee_fields.py
│
├── calculators/
│   │
│   ├── weapon_calculator.py
│   ├── ranged_calculator.py
│   ├── primary_calculator.py
│   ├── secondary_calculator.py
│   └── melee_calculator.py
│
├── formatters/
│   │
│   ├── weapon_formatter.py
│   ├── ranged_formatter.py
│   ├── primary_formatter.py
│   ├── secondary_formatter.py
│   └── melee_formatter.py
│
└── utils/
    │
    ├── constants.py
    ├── functions.py
    └── types.py
```
## Database Construction

`WarframeDatabase` is responsible for lookup and filtering, while
`DatabaseFactory` converts a `DatabaseEntry` into a public weapon or upgrade
model.

Normal values in `stats`, `conditional_stats`, and `stacking_stats` scale with
the selected rank. Static effects that unlock at a particular rank are stored
in `rank_locked_stats` as `[value, required_rank]`. The factory adds an unlocked
value to `Upgrade.stats`; it does not expose rank requirements as combat
conditions. For example, Deadhead's headshot multiplier is absent at ranks 0–4
and becomes a permanent `weakpoint_damage` stat at rank 5.
