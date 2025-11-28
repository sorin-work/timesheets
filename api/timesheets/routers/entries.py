from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import ValidationFailed
from timesheets.models import Project, TimeEntry, User
from timesheets.routers.common import get_owned
from timesheets.schemas.entries import EntryIn, EntryOut, EntryPage, EntryUpdate

router = APIRouter(prefix="/api/entries", tags=["entries"])


def _active_project(db, project_id: int, user: User) -> Project:
    project = get_owned(db, Project, project_id, user, "Project")
    if project.archived_at is not None:
        raise ValidationFailed("Cannot log time on an archived project")
    return project


def _day_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC)


@router.get("", response_model=EntryPage)
def list_entries(
    db: DbSession,
    user: CurrentUser,
    client_id: int | None = None,
    project_id: int | None = None,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    billable: bool | None = None,
    q: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> EntryPage:
    stmt = (
        select(TimeEntry)
        .join(TimeEntry.project)
        .options(joinedload(TimeEntry.project).joinedload(Project.client))
        .where(TimeEntry.user_id == user.id)
        .order_by(TimeEntry.started_at.desc(), TimeEntry.id.desc())
    )
    if client_id is not None:
        stmt = stmt.where(Project.client_id == client_id)
    if project_id is not None:
        stmt = stmt.where(TimeEntry.project_id == project_id)
    if date_from is not None:
        stmt = stmt.where(TimeEntry.started_at >= _day_start(date_from))
    if date_to is not None:
        stmt = stmt.where(TimeEntry.started_at < _day_start(date_to + timedelta(days=1)))
    if billable is not None:
        stmt = stmt.where(TimeEntry.billable.is_(billable))
    if q:
        stmt = stmt.where(TimeEntry.description.ilike(f"%{q.strip()}%"))

    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return EntryPage(
        items=[EntryOut.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, total // page_size),
    )


@router.post("", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(body: EntryIn, db: DbSession, user: CurrentUser) -> TimeEntry:
    project = _active_project(db, body.project_id, user)
    data = body.model_dump()
    if data["billable"] is None:
        data["billable"] = project.billable
    entry = TimeEntry(user_id=user.id, source="manual", **data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=EntryOut)
def get_entry(entry_id: int, db: DbSession, user: CurrentUser) -> TimeEntry:
    return get_owned(db, TimeEntry, entry_id, user, "Entry")


@router.patch("/{entry_id}", response_model=EntryOut)
def update_entry(entry_id: int, body: EntryUpdate, db: DbSession, user: CurrentUser) -> TimeEntry:
    entry = get_owned(db, TimeEntry, entry_id, user, "Entry")
    changes = body.model_dump(exclude_unset=True)
    if changes.get("project_id") is not None:
        _active_project(db, changes["project_id"], user)
    for field, value in changes.items():
        if value is None:
            continue
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, db: DbSession, user: CurrentUser) -> Response:
    entry = get_owned(db, TimeEntry, entry_id, user, "Entry")
    db.delete(entry)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
