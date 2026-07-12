from __future__ import annotations

from typing import Any, Self, Unpack

from ..utils import Condition
from ..calculators import WeaponCalculator
from ..fields import WeaponFields
from ..formatters import WeaponFormatter
from ..states import WeaponState
from .upgrade import Upgrade
from .build import Build
from .dist import dist


def _state_kwargs(kwargs: dict[str, Any], *, ranged: bool = False) -> dict[str, Any]:
    values = dict(kwargs)
    values["damage_dist"] = dist(values.pop("damage", {}))
    values["forced_procs"] = dist(values.pop("forced_procs", {}))
    if ranged:
        values["explosion_damage_dist"] = dist(values.pop("explosion_damage", {}))
        values["explosion_forced_procs"] = dist(values.pop("explosion_forced_procs", {}))
    return values


class Weapon:
    def __init__(self, **kwargs: Unpack[WeaponFields]):
        base = WeaponState(**_state_kwargs(kwargs))
        self.stats = WeaponCalculator(base)
        self.format = WeaponFormatter(self.stats)

    def configure(self, *args: Build | Upgrade, context: dict[Condition, bool | int] | None = None) -> Self:
        if all(type(arg) is Upgrade for arg in args): build = Build(*args)
        elif isinstance(args[0], Build) and len(args) == 1: build = args[0]
        else: raise TypeError
        self.stats._set_build(build, context)
        return self
