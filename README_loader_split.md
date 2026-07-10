# Loader split patch

Copy these files into `warframe_damage_calculator/data/`.

This keeps the same public API:

```python
from warframe_damage_calculator import db
weapon = db.get_weapon("Acceltra Prime")
mod = db.get_upgrade("Serration")
```

The old 1000+ line `data/loader.py` has been split into:

- `loader.py` — public `WarframeDatabase` class and `db` instance
- `constants.py` — database constants and type aliases
- `normalization.py` — name/type normalization helpers
- `paths.py` — packaged JSON paths and JSON loader
- `records.py` — `MatchResult`
- `construction.py` — model construction and upgrade payload preparation
- `access.py` — public lookup/filter methods
- `matching.py` — compatibility and requirement matching

No UI changes are needed in the Streamlit app.
