from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

FEE_PRECISION = Decimal("0.00001")
_BPS_DENOMINATOR = Decimal("10000")
_ZERO = Decimal("0")
_ONE = Decimal("1")


def fee_amount_for_buy_shares(*, shares: Decimal, price: Decimal, base_fee_bps: int) -> Decimal:
    if shares <= _ZERO or base_fee_bps <= 0:
        return _ZERO

    fee_rate = Decimal(base_fee_bps) / _BPS_DENOMINATOR
    fee = shares * fee_rate * price * (_ONE - price)
    rounded_fee = fee.quantize(FEE_PRECISION, rounding=ROUND_HALF_UP)
    if rounded_fee < FEE_PRECISION:
        return _ZERO
    return rounded_fee
