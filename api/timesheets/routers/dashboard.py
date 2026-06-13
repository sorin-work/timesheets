from collections import defaultdict
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from timesheets import clock
from timesheets.deps import CurrentUser, DbSession
from timesheets.models import Invoice, Project, TimeEntry
from timesheets.schemas.entries import EntryOut
from timesheets.schemas.reports import Amount
from timesheets.services.money import hours_from_seconds, line_amount
from timesheets.services.rounding import round_seconds

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class Dashboard(BaseModel):
    today_seconds: int
    week_seconds: int
    unbilled_seconds: int
    unbilled: list[Amount]
    outstanding: list[Amount]
    outstanding_count: int
    overdue_count: int
    recent: list[EntryOut]


@router.get("", response_model=Dashboard)
def dashboard(db: DbSession, user: CurrentUser) -> Dashboard:
    today = clock.today()
    day_start = datetime.combine(today, time.min, tzinfo=UTC)
    week_start = day_start - timedelta(days=today.weekday())

    week_entries = db.scalars(
        select(TimeEntry).where(TimeEntry.user_id == user.id, TimeEntry.started_at >= week_start)
    ).all()
    week_seconds = sum(e.duration_seconds for e in week_entries)
    today_seconds = sum(e.duration_seconds for e in week_entries if e.started_at >= day_start)

    unbilled_entries = db.scalars(
        select(TimeEntry)
        .options(joinedload(TimeEntry.project).joinedload(Project.client))
        .where(
            TimeEntry.user_id == user.id,
            TimeEntry.billable.is_(True),
            TimeEntry.invoice_id.is_(None),
            TimeEntry.ended_at.is_not(None),
        )
    ).all()
    unbilled: dict[str, Decimal] = defaultdict(Decimal)
    for entry in unbilled_entries:
        rate = entry.project.effective_rate
        if rate is not None:
            hours = hours_from_seconds(round_seconds(entry.duration_seconds, user.rounding))
            unbilled[entry.project.currency] += line_amount(hours, rate)

    open_invoices = db.scalars(
        select(Invoice).where(Invoice.user_id == user.id, Invoice.status == "sent")
    ).all()
    outstanding: dict[str, Decimal] = defaultdict(Decimal)
    for invoice in open_invoices:
        outstanding[invoice.currency] += invoice.total

    recent = db.scalars(
        select(TimeEntry)
        .options(joinedload(TimeEntry.project).joinedload(Project.client))
        .where(TimeEntry.user_id == user.id)
        .order_by(TimeEntry.started_at.desc())
        .limit(6)
    ).all()

    return Dashboard(
        today_seconds=today_seconds,
        week_seconds=week_seconds,
        unbilled_seconds=sum(e.duration_seconds for e in unbilled_entries),
        unbilled=Amount.list_from(unbilled),
        outstanding=Amount.list_from(outstanding),
        outstanding_count=len(open_invoices),
        overdue_count=sum(1 for i in open_invoices if i.is_overdue),
        recent=[EntryOut.model_validate(e) for e in recent],
    )
