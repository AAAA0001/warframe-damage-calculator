from typing import assert_type

from warframe_damage_calculator import Melee, Primary, Secondary, Upgrade, arsenal


assert_type(arsenal.get("Corinth Prime"), Primary)
assert_type(arsenal.get("Kuva Nukor"), Secondary)
assert_type(arsenal.get("Prisma Skana"), Melee)
assert_type(arsenal.get("Serration"), Upgrade)

assert_type(arsenal.get("Corinth Prime", type="primary"), Primary)
assert_type(arsenal.get(type="primary"), dict[str, Primary | Upgrade])
assert_type(arsenal.get("Kuva Nukor", type="secondary"), Secondary)
assert_type(arsenal.get(type="secondary"), dict[str, Secondary | Upgrade])
assert_type(arsenal.get("Prisma Skana", type="melee"), Melee)
assert_type(arsenal.get(type="melee"), dict[str, Melee | Upgrade])
