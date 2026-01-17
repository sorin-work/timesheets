from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from timesheets.deps import CurrentUser, DbSession
from timesheets.models import Client, Invoice
from timesheets.routers.common import get_owned
from timesheets.schemas.invoices import GenerateIn, InvoiceDetail, InvoiceSummary
from timesheets.services.invoicing import GenerateOptions, generate_invoice

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
    options = GenerateOptions(**body.model_dump())
    return generate_invoice(db, user, client, options)


@router.get("/{invoice_id}", response_model=InvoiceDetail)
def get_invoice(invoice_id: int, db: DbSession, user: CurrentUser) -> Invoice:
    return get_owned(db, Invoice, invoice_id, user, "Invoice")
