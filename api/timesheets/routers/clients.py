from datetime import UTC, datetime

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import Conflict
from timesheets.models import Client, Invoice
from timesheets.routers.common import get_owned
from timesheets.schemas.clients import ClientIn, ClientOut, ClientUpdate

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=list[ClientOut])
def list_clients(db: DbSession, user: CurrentUser, include_archived: bool = False) -> list[Client]:
    stmt = select(Client).where(Client.user_id == user.id).order_by(Client.name)
    if not include_archived:
        stmt = stmt.where(Client.archived_at.is_(None))
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
