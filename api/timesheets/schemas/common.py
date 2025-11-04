from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, Field

CURRENCIES = {"EUR", "USD", "GBP", "RON", "CHF", "CAD", "AUD", "SEK", "NOK", "DKK", "PLN", "CZK"}


def _currency(value: str) -> str:
    value = value.strip().upper()
    if value not in CURRENCIES:
        raise ValueError(f"unsupported currency, use one of {', '.join(sorted(CURRENCIES))}")
    return value


def _strip(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be blank")
    return value


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


Currency = Annotated[str, AfterValidator(_currency)]
Name = Annotated[str, Field(max_length=200), AfterValidator(_strip)]
OptionalText = Annotated[
    str | None, Field(default=None, max_length=5000), AfterValidator(_blank_to_none)
]
Rate = Annotated[Decimal, Field(ge=0, le=100000, max_digits=12, decimal_places=2)]
