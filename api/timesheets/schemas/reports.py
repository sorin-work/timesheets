from collections.abc import Mapping
from decimal import Decimal

from pydantic import BaseModel


class Amount(BaseModel):
    currency: str
    amount: Decimal

    @classmethod
    def list_from(cls, values: Mapping[str, Decimal]) -> list["Amount"]:
        """{"EUR": 10, "USD": 5} -> amounts sorted by currency, as the API returns them."""
        return [cls(currency=c, amount=a) for c, a in sorted(values.items())]


class TimeReportRow(BaseModel):
    key: str
    label: str
    tracked_seconds: int
    billable_seconds: int
    unbilled_seconds: int
    amounts: list[Amount]


class TimeReport(BaseModel):
    group_by: str
    rows: list[TimeReportRow]
    tracked_seconds: int
    billable_seconds: int
    amounts: list[Amount]


class RevenueMonthOut(BaseModel):
    month: str
    invoiced: list[Amount]
    paid: list[Amount]


class RevenueReport(BaseModel):
    year: int
    months: list[RevenueMonthOut]
    invoiced: list[Amount]
    paid: list[Amount]
