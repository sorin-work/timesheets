from datetime import UTC, datetime, time
from decimal import Decimal

from fastapi import APIRouter, Response, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import Conflict, ValidationFailed
from timesheets.models import Client, Invoice, InvoiceTax
from timesheets.routers.common import get_owned
from timesheets.schemas.invoices import (
    GenerateIn,
    InvoiceDetail,
    InvoiceSummary,
    InvoiceUpdate,
    PaymentIn,
)
from timesheets.services.invoicing import (
    GenerateOptions,
    change_status,
    generate_invoice,
    recalculate,
)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceSummary])
def list_invoices(db: DbSession, user: CurrentUser) -> list[Invoice]:
    stmt = (
        select(Invoice)
        .options(joinedload(Invoice.client))
        .where(Invoice.user_id == user.id)
        .order_by(Invoice.issue_date.desc(), Invoice.sequence.desc())
    )
    return list(db.scalars(stmt))


@router.post("/generate", response_model=InvoiceDetail, status_code=status.HTTP_201_CREATED)
def generate(body: GenerateIn, db: DbSession, user: CurrentUser) -> Invoice:
    client = get_owned(db, Client, body.client_id, user, "Client")
    options = GenerateOptions(
        **body.model_dump(exclude={"taxes"}),
        taxes=[(tax.name.strip(), tax.rate) for tax in body.taxes],
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


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: DbSession, user: CurrentUser) -> Response:
    """Delete a draft; its time entries become unbilled again."""
    invoice = _draft(db, invoice_id, user)
    for entry in invoice.entries:
        entry.invoice_id = None
    db.delete(invoice)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
