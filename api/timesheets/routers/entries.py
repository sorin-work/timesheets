import csv
import io
import math
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import joinedload

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import Conflict, NotFound, ValidationFailed
from timesheets.models import Project, TimeEntry, User
from timesheets.routers.common import get_owned
from timesheets.schemas.entries import (
    BulkIn,
    BulkOut,
    EntryIn,
    EntryOut,
    EntryPage,
    EntryUpdate,
)

router = APIRouter(prefix="/api/entries", tags=["entries"])


def _active_project(db, project_id: int, user: User) -> Project:
    project = get_owned(db, Project, project_id, user, "Project")
    if project.archived_at is not None:
        raise ValidationFailed("Cannot log time on an archived project")
    return project


def _unbilled(db, entry_id: int, user: User) -> TimeEntry:
    entry = get_owned(db, TimeEntry, entry_id, user, "Entry")
    if entry.invoice_id is not None:
        raise Conflict("This entry is on an invoice; delete the draft invoice to change it")
    return entry


def _day_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC)


@dataclass
class EntryFilters:
    client_id: int | None = None
    project_id: int | None = None
    date_from: Annotated[date | None, Query(alias="from")] = None
    date_to: Annotated[date | None, Query(alias="to")] = None
    billable: bool | None = None
    q: str | None = None


def _filtered(user: User, filters: EntryFilters) -> Select[tuple[TimeEntry]]:
    stmt = (
        select(TimeEntry)
        .join(TimeEntry.project)
        .options(joinedload(TimeEntry.project).joinedload(Project.client))
        .where(TimeEntry.user_id == user.id)
        .order_by(TimeEntry.started_at.desc(), TimeEntry.id.desc())
    )
    if filters.client_id is not None:
        stmt = stmt.where(Project.client_id == filters.client_id)
    if filters.project_id is not None:
        stmt = stmt.where(TimeEntry.project_id == filters.project_id)
    if filters.date_from is not None:
        stmt = stmt.where(TimeEntry.started_at >= _day_start(filters.date_from))
    if filters.date_to is not None:
        stmt = stmt.where(TimeEntry.started_at < _day_start(filters.date_to + timedelta(days=1)))
    if filters.billable is not None:
        stmt = stmt.where(TimeEntry.billable.is_(filters.billable))
    if filters.q:
        stmt = stmt.where(TimeEntry.description.ilike(f"%{filters.q.strip()}%"))
    return stmt


@router.get("", response_model=EntryPage)
def list_entries(
    db: DbSession,
    user: CurrentUser,
    filters: Annotated[EntryFilters, Depends()],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> EntryPage:
    stmt = _filtered(user, filters)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return EntryPage(
        items=[EntryOut.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/export.csv", response_class=Response)
def export_entries(
    db: DbSession, user: CurrentUser, filters: Annotated[EntryFilters, Depends()]
) -> Response:
    """The filtered entries as CSV, newest first, durations in decimal hours."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "date",
            "start",
            "end",
            "client",
            "project",
            "description",
            "hours",
            "billable",
            "invoiced",
        ]
    )
    for entry in db.scalars(_filtered(user, filters).where(TimeEntry.ended_at.is_not(None))):
        assert entry.ended_at is not None
        writer.writerow(
            [
                entry.started_at.date().isoformat(),
                entry.started_at.strftime("%H:%M"),
                entry.ended_at.strftime("%H:%M"),
                entry.client_name,
                entry.project_name,
                entry.description,
                f"{entry.duration_seconds / 3600:.2f}",
                "yes" if entry.billable else "no",
                "yes" if entry.invoice_id else "no",
            ]
        )
    return Response(
        buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="time-entries.csv"'},
    )


@router.post("/bulk", response_model=BulkOut)
def bulk_update(body: BulkIn, db: DbSession, user: CurrentUser) -> BulkOut:
    """Mark several entries billable or not, or delete them, all or nothing."""
    entries = list(
        db.scalars(
            select(TimeEntry).where(TimeEntry.user_id == user.id, TimeEntry.id.in_(body.ids))
        )
    )
    if len(entries) != len(set(body.ids)):
        raise NotFound("Some entries were not found")
    if any(e.invoice_id is not None for e in entries):
        raise Conflict("Some of these entries are on an invoice and cannot be changed")
    if any(e.ended_at is None for e in entries):
        raise Conflict("Stop the running timer first")
    if body.action == "delete":
        for entry in entries:
            db.delete(entry)
        db.commit()
        return BulkOut(updated=0, deleted=len(entries))
    for entry in entries:
        entry.billable = body.action == "billable"
    db.commit()
    return BulkOut(updated=len(entries), deleted=0)


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
    entry = _unbilled(db, entry_id, user)
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
    entry = _unbilled(db, entry_id, user)
    db.delete(entry)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
