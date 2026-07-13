import re
from collections.abc import Iterable


def normalize_name(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def normalize_identifier(value):
    return re.sub(r"[^a-z0-9]+", "_", normalize_name(value)).strip("_")


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return list(value)
    return [value]
