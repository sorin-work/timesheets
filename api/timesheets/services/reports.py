"""Aggregations for the reports page."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from timesheets.models import Invoice, Project, TimeEntry, User
from timesheets.services.money import hours_from_seconds, line_amount
from timesheets.services.rounding import round_seconds


@dataclass
class TimeRow:
    key: str
    label: str
    tracked_seconds: int = 0
    billable_seconds: int = 0
    unbilled_seconds: int = 0
    amounts: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))


def _group_key(entry: TimeEntry, group_by: str) -> tuple[str, str]:
    project = entry.project
    if group_by == "project":
        return str(project.id), f"{project.client.name} / {project.name}"
    if group_by == "month":
        month = entry.started_at.astimezone(UTC).strftime("%Y-%m")
        return month, month
    return str(project.client_id), project.client.name


def time_report(
    db: Session, user: User, date_from: date, date_to: date, group_by: str
) -> list[TimeRow]:
    begin = datetime.combine(date_from, time.min, tzinfo=UTC)
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
    stmt = (
        select(TimeEntry)
        .options(joinedload(TimeEntry.project).joinedload(Project.client))
        .where(
            TimeEntry.user_id == user.id,
            TimeEntry.ended_at.is_not(None),
            TimeEntry.started_at >= begin,
            TimeEntry.started_at < end,
        )
    )
    rows: dict[str, TimeRow] = {}
    for entry in db.scalars(stmt):
        key, label = _group_key(entry, group_by)
        row = rows.setdefault(key, TimeRow(key, label))
        seconds = entry.duration_seconds
        row.tracked_seconds += seconds
        if not entry.billable:
            continue
        row.billable_seconds += seconds
        if entry.invoice_id is None:
            row.unbilled_seconds += seconds
        rate = entry.project.effective_rate
        if rate is not None:
            hours = hours_from_seconds(round_seconds(seconds, user.rounding))
            row.amounts[entry.project.currency] += line_amount(hours, rate)
    ordered = sorted(rows.values(), key=lambda r: r.key if group_by == "month" else r.label.lower())
    return ordered


@dataclass
class RevenueMonth:
    month: str
    invoiced: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))
    paid: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))


def revenue_report(db: Session, user: User, year: int) -> list[RevenueMonth]:
    """Invoiced (by issue date) and paid (by payment date) totals for each month of a year.

    Drafts are not revenue yet and are left out.
    """
    months = [RevenueMonth(f"{year}-{m:02d}") for m in range(1, 13)]
    issued = select(Invoice).where(
        Invoice.user_id == user.id,
        Invoice.status != "draft",
        Invoice.issue_date >= date(year, 1, 1),
        Invoice.issue_date <= date(year, 12, 31),
    )
    for invoice in db.scalars(issued):
        months[invoice.issue_date.month - 1].invoiced[invoice.currency] += invoice.total
    paid = select(Invoice).where(
        Invoice.user_id == user.id,
        Invoice.status == "paid",
        Invoice.paid_at >= datetime(year, 1, 1, tzinfo=UTC),
        Invoice.paid_at < datetime(year + 1, 1, 1, tzinfo=UTC),
    )
    for invoice in db.scalars(paid):
        assert invoice.paid_at is not None
        months[invoice.paid_at.astimezone(UTC).month - 1].paid[invoice.currency] += invoice.total
    return months
