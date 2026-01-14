"""Turning unbilled time into invoices."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from timesheets.models import Invoice, User


def next_number(db: Session, user: User) -> tuple[int, str]:
    """Next per-user invoice sequence and its display number, e.g. (7, "INV-7")."""
    last = db.scalar(select(func.max(Invoice.sequence)).where(Invoice.user_id == user.id))
    sequence = (last or 0) + 1
    return sequence, f"{user.invoice_prefix}{sequence}"
