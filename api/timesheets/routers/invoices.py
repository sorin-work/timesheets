from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Response, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from timesheets import clock
from timesheets.deps import CurrentUser, DbSession, DownloadUser
from timesheets.errors import Conflict, NotFound, ValidationFailed
from timesheets.models import Client, Invoice, InvoiceLine, InvoiceTax
from timesheets.routers.common import get_owned
from timesheets.schemas.invoices import (
    GenerateIn,
    InvoiceDetail,
    InvoiceSummary,
    InvoiceUpdate,
    LineIn,
    PaymentIn,
    UnbilledProject,
    UnbilledSummary,
)
from timesheets.services.invoicing import (
    GenerateOptions,
    change_status,
    generate_invoice,
    recalculate,
    unbilled_entries,
)
from timesheets.services.money import line_amount
from timesheets.services.pdf import render_invoice_pdf
from timesheets.services.rounding import round_seconds

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


SORT_COLUMNS = {
    # Not Invoice.number: as text "INV-10" sorts before "INV-9".
    "number": Invoice.sequence,
    "issue_date": Invoice.issue_date,
    "due_date": Invoice.due_date,
    "total": Invoice.total,
}

InvoiceStatus = Literal["draft", "sent", "paid", "overdue"]


@router.get("", response_model=list[InvoiceSummary])
def list_invoices(
    db: DbSession,
    user: CurrentUser,
    status: InvoiceStatus | None = None,
    client_id: int | None = None,
    sort: Literal["number", "issue_date", "due_date", "total"] = "number",
    order: Literal["asc", "desc"] = "desc",
) -> list[Invoice]:
    column = SORT_COLUMNS[sort]
    stmt = (
        select(Invoice)
        .options(joinedload(Invoice.client))
        .where(Invoice.user_id == user.id)
        .order_by(column.desc() if order == "desc" else column.asc(), Invoice.id.desc())
    )
    if client_id is not None:
        stmt = stmt.where(Invoice.client_id == client_id)
    if status == "overdue":
        stmt = stmt.where(Invoice.status == "sent", Invoice.due_date < clock.today())
    elif status == "sent":
        stmt = stmt.where(Invoice.status == "sent", Invoice.due_date >= clock.today())
    elif status is not None:
        stmt = stmt.where(Invoice.status == status)
    return list(db.scalars(stmt))


@router.get("/unbilled", response_model=UnbilledSummary)
def unbilled_summary(
    db: DbSession,
    user: CurrentUser,
    client_id: int,
    period_start: date,
    period_end: date,
) -> UnbilledSummary:
    """Preview of what an invoice for this client and period would contain."""
    client = get_owned(db, Client, client_id, user, "Client")
    entries = unbilled_entries(db, user, client.id, period_start, period_end)
    projects: dict[int, UnbilledProject] = {}
    for entry in entries:
        rounded = round_seconds(entry.duration_seconds, user.rounding)
        row = projects.get(entry.project_id)
        if row is None:
            row = projects[entry.project_id] = UnbilledProject(
                project_id=entry.project_id,
                project_name=entry.project.name,
                hourly_rate=entry.project.effective_rate,
                entries=0,
                seconds=0,
                billable_seconds=0,
            )
        row.entries += 1
        row.seconds += entry.duration_seconds
        row.billable_seconds += rounded
    return UnbilledSummary(
        client_id=client.id,
        currency=client.currency,
        projects=sorted(projects.values(), key=lambda p: p.project_name.lower()),
    )


@router.post("/generate", response_model=InvoiceDetail, status_code=status.HTTP_201_CREATED)
def generate(body: GenerateIn, db: DbSession, user: CurrentUser) -> Invoice:
    client = get_owned(db, Client, body.client_id, user, "Client")
    options = GenerateOptions(
        **body.model_dump(exclude={"taxes"}),
        taxes=[(tax.name.strip(), tax.rate) for tax in body.taxes]
        if body.taxes is not None
        else [(t["name"], Decimal(t["rate"])) for t in user.default_taxes],
    )
    return generate_invoice(db, user, client, options)


@router.get("/{invoice_id}", response_model=InvoiceDetail)
def get_invoice(invoice_id: int, db: DbSession, user: CurrentUser) -> Invoice:
    return get_owned(db, Invoice, invoice_id, user, "Invoice")


@router.post("/{invoice_id}/send", response_model=InvoiceDetail)
def send_invoice(invoice_id: int, db: DbSession, user: CurrentUser) -> Invoice:
    """Mark the invoice as sent. Sent invoices are locked against edits."""
    invoice = get_owned(db, Invoice, invoice_id, user, "Invoice")
    change_status(db, invoice, "send")
    return invoice


@router.post("/{invoice_id}/pay", response_model=InvoiceDetail)
def pay_invoice(
    invoice_id: int, db: DbSession, user: CurrentUser, body: PaymentIn | None = None
) -> Invoice:
    invoice = get_owned(db, Invoice, invoice_id, user, "Invoice")
    when = None
    if body is not None and body.paid_on is not None:
        when = datetime.combine(body.paid_on, time(12), tzinfo=UTC)
    change_status(db, invoice, "pay", when)
    return invoice


@router.post("/{invoice_id}/unpay", response_model=InvoiceDetail)
def unpay_invoice(invoice_id: int, db: DbSession, user: CurrentUser) -> Invoice:
    invoice = get_owned(db, Invoice, invoice_id, user, "Invoice")
    change_status(db, invoice, "unpay")
    return invoice


@router.post("/{invoice_id}/revert", response_model=InvoiceDetail)
def revert_invoice(invoice_id: int, db: DbSession, user: CurrentUser) -> Invoice:
    """Back to draft, e.g. when it was marked sent by mistake."""
    invoice = get_owned(db, Invoice, invoice_id, user, "Invoice")
    change_status(db, invoice, "revert")
    return invoice


def _draft(db, invoice_id: int, user) -> Invoice:
    invoice = get_owned(db, Invoice, invoice_id, user, "Invoice")
    if invoice.status != "draft":
        raise Conflict("Only draft invoices can be changed")
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceDetail)
def update_invoice(
    invoice_id: int, body: InvoiceUpdate, db: DbSession, user: CurrentUser
) -> Invoice:
    invoice = _draft(db, invoice_id, user)
    changes = body.model_dump(exclude_unset=True)
    if "notes" in changes:
        invoice.notes = changes["notes"]
    if "reference" in changes:
        invoice.reference = (changes["reference"] or "").strip() or None
    if changes.get("issue_date"):
        invoice.issue_date = changes["issue_date"]
    if changes.get("due_date"):
        invoice.due_date = changes["due_date"]
    if invoice.due_date < invoice.issue_date:
        raise ValidationFailed("The due date cannot be before the issue date")
    if body.taxes is not None:
        invoice.taxes = [
            InvoiceTax(name=t.name.strip(), rate=t.rate, amount=Decimal("0.00")) for t in body.taxes
        ]
    recalculate(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/lines", response_model=InvoiceDetail, status_code=201)
def add_line(invoice_id: int, body: LineIn, db: DbSession, user: CurrentUser) -> Invoice:
    invoice = _draft(db, invoice_id, user)
    invoice.lines.append(
        InvoiceLine(
            description=body.description.strip(),
            quantity=body.quantity,
            unit_price=body.unit_price,
            amount=line_amount(body.quantity, body.unit_price),
            position=max((line.position for line in invoice.lines), default=-1) + 1,
        )
    )
    recalculate(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.delete("/{invoice_id}/lines/{line_id}", response_model=InvoiceDetail)
def delete_line(invoice_id: int, line_id: int, db: DbSession, user: CurrentUser) -> Invoice:
    invoice = _draft(db, invoice_id, user)
    line = next((li for li in invoice.lines if li.id == line_id), None)
    if line is None:
        raise NotFound("Line not found")
    if line.project_id is not None:
        raise Conflict("Lines for tracked time go away with the draft; delete the draft instead")
    invoice.lines.remove(line)
    recalculate(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: DbSession, user: CurrentUser) -> Response:
    """Delete a draft; its time entries become unbilled again."""
    invoice = _draft(db, invoice_id, user)
    for entry in invoice.entries:
        entry.invoice_id = None
    db.delete(invoice)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{invoice_id}/pdf", response_class=Response)
def invoice_pdf(invoice_id: int, db: DbSession, user: DownloadUser) -> Response:
    invoice = get_owned(db, Invoice, invoice_id, user, "Invoice")
    filename = f"{invoice.number}.pdf".replace("/", "-")
    return Response(
        render_invoice_pdf(invoice, user),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
