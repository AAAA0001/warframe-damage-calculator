from __future__ import annotations

from typing import Any
import re


def normalized_key(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def normalized_slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", normalized_key(value)).strip("_")


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    return [value]
