from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import Conflict
from timesheets.models import Client, Invoice, Project, TimeEntry
from timesheets.routers.common import get_owned
from timesheets.schemas.clients import ClientIn, ClientOut, ClientSummary, ClientUpdate

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=list[ClientOut])
def list_clients(
    db: DbSession, user: CurrentUser, include_archived: bool = False, q: str | None = None
) -> list[Client]:
    stmt = select(Client).where(Client.user_id == user.id).order_by(func.lower(Client.name))
    if not include_archived:
        stmt = stmt.where(Client.archived_at.is_(None))
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(Client.name.ilike(pattern) | Client.email.ilike(pattern))
    return list(db.scalars(stmt))


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(body: ClientIn, db: DbSession, user: CurrentUser) -> Client:
    client = Client(user_id=user.id, **body.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: DbSession, user: CurrentUser) -> Client:
    return get_owned(db, Client, client_id, user, "Client")


@router.get("/{client_id}/summary", response_model=ClientSummary)
def client_summary(client_id: int, db: DbSession, user: CurrentUser) -> ClientSummary:
    """Totals for the client page: time tracked and money invoiced, paid and owed."""
    client = get_owned(db, Client, client_id, user, "Client")
    seconds = func.coalesce(
        func.sum(func.extract("epoch", TimeEntry.ended_at - TimeEntry.started_at)), 0
    )
    entries = (
        select(TimeEntry)
        .join(TimeEntry.project)
        .where(Project.client_id == client.id, TimeEntry.ended_at.is_not(None))
        .subquery()
    )
    tracked, last = db.execute(
        select(
            func.coalesce(
                func.sum(func.extract("epoch", entries.c.ended_at - entries.c.started_at)), 0
            ),
            func.max(entries.c.started_at),
        )
    ).one()
    unbilled = db.scalar(
        select(seconds)
        .join(TimeEntry.project)
        .where(
            Project.client_id == client.id,
            TimeEntry.ended_at.is_not(None),
            TimeEntry.billable.is_(True),
            TimeEntry.invoice_id.is_(None),
        )
    )
    totals = dict(
        db.execute(
            select(Invoice.status, func.sum(Invoice.total))
            .where(Invoice.client_id == client.id, Invoice.status != "draft")
            .group_by(Invoice.status)
        ).all()
    )
    paid = totals.get("paid") or Decimal("0.00")
    outstanding = totals.get("sent") or Decimal("0.00")
    return ClientSummary(
        client_id=client.id,
        currency=client.currency,
        projects=db.scalar(select(func.count()).where(Project.client_id == client.id)) or 0,
        tracked_seconds=int(tracked),
        unbilled_seconds=int(unbilled or 0),
        last_tracked_at=last,
        invoiced=paid + outstanding,
        paid=paid,
        outstanding=outstanding,
    )


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, body: ClientUpdate, db: DbSession, user: CurrentUser) -> Client:
    client = get_owned(db, Client, client_id, user, "Client")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field in ("name", "currency") and value is None:
            continue
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: DbSession, user: CurrentUser) -> Response:
    client = get_owned(db, Client, client_id, user, "Client")
    if db.scalar(select(Invoice.id).where(Invoice.client_id == client.id).limit(1)):
        raise Conflict("This client has invoices; archive it instead")
    db.delete(client)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{client_id}/archive", response_model=ClientOut)
def archive_client(client_id: int, db: DbSession, user: CurrentUser) -> Client:
    """Hide a client from pickers while keeping its projects, entries and invoices."""
    client = get_owned(db, Client, client_id, user, "Client")
    if client.archived_at is None:
        client.archived_at = datetime.now(UTC)
        db.commit()
    return client


@router.post("/{client_id}/restore", response_model=ClientOut)
def restore_client(client_id: int, db: DbSession, user: CurrentUser) -> Client:
    client = get_owned(db, Client, client_id, user, "Client")
    client.archived_at = None
    db.commit()
    return client
