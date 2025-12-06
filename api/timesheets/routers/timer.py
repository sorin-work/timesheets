from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import Conflict
from timesheets.models import TimeEntry
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


@router.post("/stop", response_model=EntryOut)
def stop_timer(db: DbSession, user: CurrentUser) -> TimeEntry:
    entry = running_entry(db, user.id)
    if entry is None:
        raise Conflict("No timer is running")
    entry.ended_at = datetime.now(UTC)
    db.commit()
    db.refresh(entry)
    return entry
