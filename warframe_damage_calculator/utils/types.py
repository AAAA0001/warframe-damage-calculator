from typing import Literal

type Stat = str
type Context = str
type Key = str

type Number = int | float
type Value = str | int | float | bool
type DamageType = Literal["impact", "puncture", "slash", "blast", "corrosive", "gas", "magnetic", "radiation", "viral", "cold", "electricity", "heat", "toxin"]