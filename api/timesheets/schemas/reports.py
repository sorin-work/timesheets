from decimal import Decimal

from pydantic import BaseModel


class Amount(BaseModel):
    currency: str
    amount: Decimal


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
