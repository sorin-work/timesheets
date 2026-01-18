from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from timesheets.config import get_settings
from timesheets.db import get_db
from timesheets.models import User
from timesheets.security import decode_access_token

DbSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False)


def _user_for_token(db: Session, token: str | None) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise unauthorized
    user_id = decode_access_token(token, get_settings().secret_key)
    if user_id is None:
        raise unauthorized
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    return _user_for_token(db, credentials.credentials if credentials else None)


def get_download_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    token: Annotated[
        str | None, Query(description="Access token, for plain download links")
    ] = None,
) -> User:
    """Like get_current_user, but also accepts ?token= so <a href> downloads work."""
    return _user_for_token(db, credentials.credentials if credentials else token)


CurrentUser = Annotated[User, Depends(get_current_user)]
DownloadUser = Annotated[User, Depends(get_download_user)]
