from typing import Annotated
from zoneinfo import available_timezones

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from timesheets.schemas.common import Currency, Name, OptionalText
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
    business_name: str | None
    business_address: str | None
    tax_id: str | None
    invoice_prefix: str
    payment_terms_days: int


class SettingsUpdate(BaseModel):
    name: Name | None = None
    timezone: TimeZone | None = None
    rounding: Rounding | None = None
    currency: Currency | None = None
    business_name: OptionalText = None
    business_address: OptionalText = None
    tax_id: OptionalText = None
    invoice_prefix: Annotated[str, Field(pattern=r"^[A-Za-z0-9/_-]{0,16}$")] | None = None
    payment_terms_days: Annotated[int, Field(ge=0, le=365)] | None = None
