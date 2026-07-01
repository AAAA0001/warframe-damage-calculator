from decimal import ROUND_HALF_UP, Decimal

def true_round(number: float, decimals: int = 0) -> float:
    quant = Decimal("1").scaleb(-decimals)
    return float(Decimal(str(number)).quantize(quant, rounding=ROUND_HALF_UP))