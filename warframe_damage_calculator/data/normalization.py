from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any


def normalize_name(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def normalize_identifier(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", normalize_name(value)).strip("_")


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return list(value)
    return [value]


# Backwards-compatible aliases for code that imported the old helper names.
normalized_key = normalize_name
normalized_slug = normalize_identifier
