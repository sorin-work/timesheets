from decimal import Decimal
from typing import Annotated
from zoneinfo import available_timezones

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from timesheets.schemas.common import Currency, Name, OptionalText
from timesheets.schemas.invoices import TaxIn
from timesheets.services.rounding import Rounding


def _timezone(value: str) -> str:
    if value not in available_timezones():
        raise ValueError("unknown time zone")
    return value


TimeZone = Annotated[str, AfterValidator(_timezone)]


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: str
    timezone: str
    rounding: Rounding
    currency: str
    weekly_target_hours: Decimal | None
    business_name: str | None
    business_address: str | None
    tax_id: str | None
    payment_details: str | None
    invoice_prefix: str
    payment_terms_days: int
    default_taxes: list[TaxIn]


class SettingsUpdate(BaseModel):
    name: Name | None = None
    timezone: TimeZone | None = None
    rounding: Rounding | None = None
    currency: Currency | None = None
    weekly_target_hours: Annotated[Decimal, Field(gt=0, le=168, decimal_places=2)] | None = None
    business_name: OptionalText = None
    business_address: OptionalText = None
    tax_id: OptionalText = None
    payment_details: OptionalText = None
    invoice_prefix: Annotated[str, Field(pattern=r"^[A-Za-z0-9/_-]{0,16}$")] | None = None
    payment_terms_days: Annotated[int, Field(ge=0, le=365)] | None = None
    default_taxes: Annotated[list[TaxIn], Field(max_length=5)] | None = None
