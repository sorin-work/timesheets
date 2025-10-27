from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from timesheets.config import get_settings
from timesheets.deps import CurrentUser, DbSession
from timesheets.models import User
from timesheets.schemas.auth import LoginIn, SignupIn, TokenOut, UserOut
from timesheets.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token_for(user: User) -> TokenOut:
    settings = get_settings()
    token = create_access_token(user.id, settings.secret_key, settings.token_ttl_minutes)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupIn, db: DbSession) -> TokenOut:
    if db.scalar(select(User.id).where(User.email == body.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return _token_for(user)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: DbSession) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return _token_for(user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user
