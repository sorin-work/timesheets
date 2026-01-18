from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from timesheets.schemas.common import OptionalText


class TaxIn(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=60)]
    rate: Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]


class GenerateIn(BaseModel):
    client_id: int
    period_start: date
    period_end: date
    project_ids: list[int] | None = None
    group_by: Literal["project", "entry"] = "project"
    issue_date: date | None = None
    due_days: Annotated[int, Field(ge=0, le=365)] | None = None
    notes: OptionalText = None
    taxes: Annotated[list[TaxIn], Field(max_length=5)] = []


class InvoiceLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int | None
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


class InvoiceTaxOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    rate: Decimal
    amount: Decimal


class InvoiceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    client_id: int
    client_name: str
    status: str = Field(validation_alias="display_status")
    issue_date: date
    due_date: date
    currency: str
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal


class InvoiceDetail(InvoiceSummary):
    period_start: date | None
    period_end: date | None
    notes: str | None
    sent_at: datetime | None
    paid_at: datetime | None
    lines: list[InvoiceLineOut]
    taxes: list[InvoiceTaxOut]
    entry_count: int


class PaymentIn(BaseModel):
    paid_on: date | None = None


class InvoiceUpdate(BaseModel):
    issue_date: date | None = None
    due_date: date | None = None
    notes: OptionalText = None
    taxes: Annotated[list[TaxIn], Field(max_length=5)] | None = None
