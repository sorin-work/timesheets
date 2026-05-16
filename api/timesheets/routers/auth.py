from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select

from timesheets.config import get_settings
from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import ValidationFailed
from timesheets.models import Invoice, User
from timesheets.ratelimit import limit_auth
from timesheets.schemas.auth import (
    DeleteAccountIn,
    LoginIn,
    PasswordChangeIn,
    SignupIn,
    TokenOut,
    UserOut,
)
from timesheets.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token_for(user: User) -> TokenOut:
    settings = get_settings()
    token = create_access_token(user.id, settings.secret_key, settings.token_ttl_minutes)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post(
    "/signup",
    response_model=TokenOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_auth)],
)
def signup(body: SignupIn, db: DbSession) -> TokenOut:
    if db.scalar(select(User.id).where(User.email == body.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return _token_for(user)


@router.post("/login", response_model=TokenOut, dependencies=[Depends(limit_auth)])
def login(body: LoginIn, db: DbSession) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return _token_for(user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(body: PasswordChangeIn, db: DbSession, user: CurrentUser) -> Response:
    if not verify_password(body.current_password, user.password_hash):
        raise ValidationFailed(
            "Current password is incorrect",
            [{"field": "current_password", "message": "Current password is incorrect"}],
        )
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(body: DeleteAccountIn, db: DbSession, user: CurrentUser) -> Response:
    """Delete the account and everything in it. Asks for the password again."""
    if not verify_password(body.password, user.password_hash):
        raise ValidationFailed(
            "Password is incorrect", [{"field": "password", "message": "Password is incorrect"}]
        )
    # Invoices first: they reference clients, which do not cascade into them.
    db.execute(delete(Invoice).where(Invoice.user_id == user.id))
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
