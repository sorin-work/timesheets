from fastapi import APIRouter

from timesheets.deps import CurrentUser, DbSession
from timesheets.models import User
from timesheets.schemas.settings import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])

REQUIRED = {"name", "timezone", "rounding", "currency", "invoice_prefix", "payment_terms_days"}


@router.get("", response_model=SettingsOut)
def get_settings(user: CurrentUser) -> User:
    return user


@router.patch("", response_model=SettingsOut)
def update_settings(body: SettingsUpdate, db: DbSession, user: CurrentUser) -> User:
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is None and field in REQUIRED:
            continue
        if field == "rounding":
            value = value.value
        elif field == "default_taxes":
            value = [{"name": t["name"].strip(), "rate": str(t["rate"])} for t in value or []]
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
