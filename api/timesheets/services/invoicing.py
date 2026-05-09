"""Turning unbilled time into invoices."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from timesheets import clock
from timesheets.errors import Conflict, ValidationFailed
from timesheets.models import (
    Client,
    Invoice,
    InvoiceLine,
    InvoiceTax,
    Project,
    TimeEntry,
    User,
)
from timesheets.services.money import hours_from_seconds, line_amount, to_money
from timesheets.services.rounding import round_seconds


@dataclass
class GenerateOptions:
    client_id: int
    period_start: date
    period_end: date
    project_ids: list[int] | None = None
    group_by: str = "project"  # or "entry"
    issue_date: date | None = None
    due_days: int | None = None
    notes: str | None = None
    taxes: list[tuple[str, Decimal]] = field(default_factory=list)


def next_number(db: Session, user: User) -> tuple[int, str]:
    """Next per-user invoice sequence and its display number, e.g. (7, "INV-7")."""
    last = db.scalar(select(func.max(Invoice.sequence)).where(Invoice.user_id == user.id))
    sequence = (last or 0) + 1
    return sequence, f"{user.invoice_prefix}{sequence}"


def unbilled_entries(
    db: Session,
    user: User,
    client_id: int,
    period_start: date,
    period_end: date,
    project_ids: list[int] | None = None,
) -> list[TimeEntry]:
    begin = datetime.combine(period_start, time.min, tzinfo=UTC)
    end = datetime.combine(period_end + timedelta(days=1), time.min, tzinfo=UTC)
    stmt = (
        select(TimeEntry)
        .join(TimeEntry.project)
        .options(joinedload(TimeEntry.project).joinedload(Project.client))
        .where(
            TimeEntry.user_id == user.id,
            Project.client_id == client_id,
            TimeEntry.billable.is_(True),
            TimeEntry.invoice_id.is_(None),
            TimeEntry.ended_at.is_not(None),
            TimeEntry.started_at >= begin,
            TimeEntry.started_at < end,
        )
        .order_by(TimeEntry.started_at, TimeEntry.id)
    )
    if project_ids:
        stmt = stmt.where(TimeEntry.project_id.in_(project_ids))
    return list(db.scalars(stmt))


def _rate(project: Project) -> Decimal:
    rate = project.effective_rate
    if rate is None:
        raise ValidationFailed(
            f"Set an hourly rate on project '{project.name}' or its client first"
        )
    return rate


def _build_lines(entries: list[TimeEntry], rounding: str, group_by: str) -> list[InvoiceLine]:
    lines: list[InvoiceLine] = []
    if group_by == "entry":
        for entry in entries:
            rate = _rate(entry.project)
            hours = hours_from_seconds(round_seconds(entry.duration_seconds, rounding))
            label = entry.description or entry.project.name
            lines.append(
                InvoiceLine(
                    project_id=entry.project_id,
                    description=f"{entry.started_at:%Y-%m-%d} {label}",
                    quantity=hours,
                    unit_price=rate,
                    amount=line_amount(hours, rate),
                )
            )
    else:
        by_project: dict[int, list[TimeEntry]] = defaultdict(list)
        for entry in entries:
            by_project[entry.project_id].append(entry)
        for project_entries in by_project.values():
            project = project_entries[0].project
            rate = _rate(project)
            seconds = sum(round_seconds(e.duration_seconds, rounding) for e in project_entries)
            hours = hours_from_seconds(seconds)
            lines.append(
                InvoiceLine(
                    project_id=project.id,
                    description=project.name,
                    quantity=hours,
                    unit_price=rate,
                    amount=line_amount(hours, rate),
                )
            )
        lines.sort(key=lambda line: line.description.lower())
    for position, line in enumerate(lines):
        line.position = position
    return lines


def tax_amount(subtotal: Decimal, rate: Decimal) -> Decimal:
    # Not round(): on Decimals it rounds half to even, so 4.545 became 4.54.
    return to_money(subtotal * rate / 100)


def recalculate(invoice: Invoice) -> None:
    """Refresh subtotal, every tax line and the total from the invoice lines."""
    invoice.subtotal = to_money(sum((line.amount for line in invoice.lines), Decimal(0)))
    for tax in invoice.taxes:
        tax.amount = tax_amount(invoice.subtotal, tax.rate)
    invoice.tax_total = to_money(sum((tax.amount for tax in invoice.taxes), Decimal(0)))
    invoice.total = invoice.subtotal + invoice.tax_total


def generate_invoice(db: Session, user: User, client: Client, options: GenerateOptions) -> Invoice:
    if options.period_end < options.period_start:
        raise ValidationFailed("period_end must not be before period_start")
    entries = unbilled_entries(
        db, user, client.id, options.period_start, options.period_end, options.project_ids
    )
    if not entries:
        raise ValidationFailed("There is no unbilled billable time for this client in the period")

    issue_date = options.issue_date or clock.today()
    due_days = user.payment_terms_days if options.due_days is None else options.due_days
    sequence, number = next_number(db, user)
    invoice = Invoice(
        user_id=user.id,
        client_id=client.id,
        number=number,
        sequence=sequence,
        status="draft",
        issue_date=issue_date,
        due_date=issue_date + timedelta(days=due_days),
        period_start=options.period_start,
        period_end=options.period_end,
        currency=client.currency,
        notes=options.notes,
    )
    invoice.lines = _build_lines(entries, user.rounding, options.group_by)
    invoice.taxes = [InvoiceTax(name=name, rate=rate) for name, rate in options.taxes]
    recalculate(invoice)
    db.add(invoice)
    db.flush()
    for entry in entries:
        entry.invoice_id = invoice.id
    db.commit()
    db.refresh(invoice)
    return invoice


TRANSITIONS = {
    "send": ({"draft"}, "sent"),
    "pay": ({"sent"}, "paid"),
    "unpay": ({"paid"}, "sent"),
    "revert": ({"sent"}, "draft"),
}


def change_status(db: Session, invoice: Invoice, action: str, when: datetime | None = None) -> None:
    allowed_from, target = TRANSITIONS[action]
    if invoice.status not in allowed_from:
        raise Conflict(f"Cannot {action} an invoice that is {invoice.status}")
    when = when or datetime.now(UTC)
    invoice.status = target
    if action == "send":
        invoice.sent_at = when
    elif action == "pay":
        invoice.paid_at = when
    elif action == "unpay":
        invoice.paid_at = None
    elif action == "revert":
        invoice.sent_at = None
    db.commit()
