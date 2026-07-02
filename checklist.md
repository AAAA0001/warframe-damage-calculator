# Feature checklist
- add doc strings

# Asumption checklist
- if internal bleeding and hunter munitions trigger at the same time only the highest damage proc occurs (source: wiki)
- secondary encumber scales with: total damage, status damage, faction damage and crit damage (source: none)
- secondary encumber can trigger hemorrage (internal bleeding) (source: none)
- secondary encumber only procs once per shot (source: wiki)
- weapon fire cicle works like this (source: testing)
    wait [charge time] seconds
    [bullet count] -= 1 - [ammo efficiency]
    if [bullet count] = 0 wait [reload time] seconds
    else wait 1 / [fire rate] seconds
    repeat