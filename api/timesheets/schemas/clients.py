from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr

from timesheets.schemas.common import Currency, Name, OptionalText, Rate


class ClientIn(BaseModel):
    name: Name
    email: EmailStr | None = None
    address: OptionalText = None
    currency: Currency = "EUR"
    hourly_rate: Rate | None = None
    notes: OptionalText = None


class ClientUpdate(BaseModel):
    name: Name | None = None
    email: EmailStr | None = None
    address: OptionalText = None
    currency: Currency | None = None
    hourly_rate: Rate | None = None
    notes: OptionalText = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None
    address: str | None
    currency: str
    hourly_rate: Decimal | None
    notes: str | None
    archived_at: datetime | None
    created_at: datetime
