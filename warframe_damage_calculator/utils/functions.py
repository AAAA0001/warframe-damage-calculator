from decimal import ROUND_HALF_UP, Decimal
from math import expm1, log1p

from .types import Number


def true_round(number: Number, decimals: Number = 0):
    quant = Decimal("1").scaleb(-decimals)
    return float(Decimal(str(number)).quantize(quant, rounding=ROUND_HALF_UP))


def clamp(value: Number, minimum: Number | None = None, maximum: Number | None = None):
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def expected_distinct_count(probabilities: dict[str, float], attempts: float, maximum: int) -> float:
    distribution = [1.0] + [0.0] * maximum
    for probability in probabilities.values():
        if probability <= 0:
            continue
        acquired = 1.0 if probability >= 1 else -expm1(attempts * log1p(-probability))
        updated = [0.0] * (maximum + 1)
        for count, state_probability in enumerate(distribution):
            updated[count] += state_probability * (1 - acquired)
            updated[min(count + 1, maximum)] += state_probability * acquired
        distribution = updated
    return sum(count * probability for count, probability in enumerate(distribution))
