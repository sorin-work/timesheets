from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Query

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import ValidationFailed
from timesheets.schemas.reports import (
    Amount,
    RevenueMonthOut,
    RevenueReport,
    TimeReport,
    TimeReportRow,
)
from timesheets.services.reports import revenue_report, time_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/time", response_model=TimeReport)
def get_time_report(
    db: DbSession,
    user: CurrentUser,
    date_from: Annotated[date, Query(alias="from")],
    date_to: Annotated[date, Query(alias="to")],
    group_by: Literal["client", "project", "month"] = "client",
    client_id: int | None = None,
) -> TimeReport:
    if date_to < date_from:
        raise ValidationFailed("'to' must not be before 'from'")
    if (date_to - date_from).days > 366 * 3:
        raise ValidationFailed("Reports can cover at most three years")
    rows = time_report(db, user, date_from, date_to, group_by, client_id)
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        for currency, amount in row.amounts.items():
            totals[currency] += amount
    return TimeReport(
        group_by=group_by,
        rows=[
            TimeReportRow(
                key=row.key,
                label=row.label,
                tracked_seconds=row.tracked_seconds,
                billable_seconds=row.billable_seconds,
                unbilled_seconds=row.unbilled_seconds,
                amounts=Amount.list_from(row.amounts),
            )
            for row in rows
        ],
        tracked_seconds=sum(r.tracked_seconds for r in rows),
        billable_seconds=sum(r.billable_seconds for r in rows),
        amounts=Amount.list_from(totals),
    )


@router.get("/revenue", response_model=RevenueReport)
def get_revenue_report(
    db: DbSession,
    user: CurrentUser,
    year: Annotated[int, Query(ge=2000, le=2100)],
) -> RevenueReport:
    months = revenue_report(db, user, year)
    invoiced: dict[str, Decimal] = defaultdict(Decimal)
    paid: dict[str, Decimal] = defaultdict(Decimal)
    for month in months:
        for currency, amount in month.invoiced.items():
            invoiced[currency] += amount
        for currency, amount in month.paid.items():
            paid[currency] += amount
    return RevenueReport(
        year=year,
        months=[
            RevenueMonthOut(
                month=m.month, invoiced=Amount.list_from(m.invoiced), paid=Amount.list_from(m.paid)
            )
            for m in months
        ],
        invoiced=Amount.list_from(invoiced),
        paid=Amount.list_from(paid),
    )
