from sqlalchemy.orm import Session

from timesheets.errors import NotFound
from timesheets.models import User


def get_owned[T](db: Session, model: type[T], obj_id: int, user: User, label: str) -> T:
    """Load a row that belongs to the user, or raise a 404 (never leak other users' ids)."""
    obj = db.get(model, obj_id)
    if obj is None or getattr(obj, "user_id", None) != user.id:
        raise NotFound(f"{label} not found")
    return obj
