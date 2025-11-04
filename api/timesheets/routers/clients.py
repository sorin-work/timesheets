from fastapi import APIRouter, Response, status
from sqlalchemy import select

from timesheets.deps import CurrentUser, DbSession
from timesheets.models import Client
from timesheets.routers.common import get_owned
from timesheets.schemas.clients import ClientIn, ClientOut, ClientUpdate

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=list[ClientOut])
def list_clients(db: DbSession, user: CurrentUser) -> list[Client]:
    stmt = select(Client).where(Client.user_id == user.id).order_by(Client.name)
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
    db.delete(client)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
