from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import AwareDatetime, BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import Conflict, ValidationFailed
from timesheets.models import TimeEntry, User
from timesheets.routers.common import get_owned
from timesheets.routers.entries import _active_project
from timesheets.schemas.entries import Description, EntryOut

router = APIRouter(prefix="/api/timer", tags=["timer"])


class TimerStart(BaseModel):
    project_id: int
    description: Description = ""
    billable: bool | None = None


class TimerUpdate(BaseModel):
    project_id: int | None = None
    description: Description | None = None
    billable: bool | None = None


def running_entry(db, user_id: int) -> TimeEntry | None:
    stmt = select(TimeEntry).where(TimeEntry.user_id == user_id, TimeEntry.ended_at.is_(None))
    return db.scalar(stmt)


@router.get("", response_model=EntryOut | None)
def current_timer(db: DbSession, user: CurrentUser) -> TimeEntry | None:
    return running_entry(db, user.id)


@router.post("/start", response_model=EntryOut, status_code=201)
def start_timer(body: TimerStart, db: DbSession, user: CurrentUser) -> TimeEntry:
    return start(db, user, body)


@router.post("/continue/{entry_id}", response_model=EntryOut, status_code=201)
def continue_entry(entry_id: int, db: DbSession, user: CurrentUser) -> TimeEntry:
    """Start a new timer with the project, description and billable flag of an entry."""
    entry = get_owned(db, TimeEntry, entry_id, user, "Entry")
    body = TimerStart(
        project_id=entry.project_id, description=entry.description, billable=entry.billable
    )
    return start(db, user, body)


def start(db, user: User, body: TimerStart) -> TimeEntry:
    project = _active_project(db, body.project_id, user)
    now = datetime.now(UTC)
    previous = running_entry(db, user.id)
    if previous is not None:
        # Switching tasks: close the running entry where the new one begins.
        previous.ended_at = now
        db.flush()
    entry = TimeEntry(
        user_id=user.id,
        project_id=project.id,
        started_at=now,
        description=body.description.strip(),
        billable=project.billable if body.billable is None else body.billable,
        source="timer",
    )
    db.add(entry)
    try:
        db.commit()
    except IntegrityError as exc:  # a parallel request started another timer
        db.rollback()
        raise Conflict("A timer is already running") from exc
    db.refresh(entry)
    return entry


@router.patch("", response_model=EntryOut)
def update_timer(body: TimerUpdate, db: DbSession, user: CurrentUser) -> TimeEntry:
    entry = running_entry(db, user.id)
    if entry is None:
        raise Conflict("No timer is running")
    if body.description is not None:
        entry.description = body.description.strip()
    if body.billable is not None:
        entry.billable = body.billable
    if body.project_id is not None:
        entry.project_id = _active_project(db, body.project_id, user).id
    db.commit()
    db.refresh(entry)
    return entry


class TimerStop(BaseModel):
    # For a timer that was left running: stop it at the time you actually finished.
    ended_at: AwareDatetime | None = None


@router.post("/stop", response_model=EntryOut)
def stop_timer(db: DbSession, user: CurrentUser, body: TimerStop | None = None) -> TimeEntry:
    entry = running_entry(db, user.id)
    if entry is None:
        raise Conflict("No timer is running")
    now = datetime.now(UTC)
    ended_at = body.ended_at if body and body.ended_at else now
    if ended_at <= entry.started_at or ended_at > now:
        raise ValidationFailed("The stop time must be between the start and now")
    entry.ended_at = ended_at
    db.commit()
    db.refresh(entry)
    return entry
