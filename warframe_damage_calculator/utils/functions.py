from decimal import ROUND_HALF_UP, Decimal


def true_round(number, decimals=0):
    quant = Decimal("1").scaleb(-decimals)
    return float(Decimal(str(number)).quantize(quant, rounding=ROUND_HALF_UP))


def clamp(value, minimum=None, maximum=None):
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value
