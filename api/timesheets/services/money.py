"""Money is always Decimal, rounded half-up to cents at the edges."""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def hours_from_seconds(seconds: int) -> Decimal:
    """Billable quantity in hours with two decimals (0.01 h = 36 s)."""
    return (Decimal(seconds) / Decimal(3600)).quantize(CENT, rounding=ROUND_HALF_UP)


def line_amount(hours: Decimal, rate: Decimal) -> Decimal:
    return to_money(hours * rate)


def format_money(amount: Decimal, currency: str) -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}{abs(to_money(amount)):,.2f} {currency}"
