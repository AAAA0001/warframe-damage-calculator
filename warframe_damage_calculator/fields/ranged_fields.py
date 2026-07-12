from ..utils import DamageType
from .weapon_fields import WeaponFields


class RangedFields(WeaponFields):
    trigger: str | None
    is_beam: bool
    is_battery: bool
    explosion_damage: dict[DamageType, float]
    explosion_forced_procs: dict[DamageType, float]
    multishot: float
    fire_rate: float
    burst_count: int
    burst_delay: float
    charge_time: float
    reload_speed: float
    recharge_rate: float
    magazine_capacity: int
    weakpoint_damage: float
