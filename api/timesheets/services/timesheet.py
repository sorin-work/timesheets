"""Weekly timesheet: seconds per project per day, Monday to Sunday."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from timesheets.models import Project, TimeEntry, User


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


@dataclass
class Row:
    project: Project
    seconds: list[int] = field(default_factory=lambda: [0] * 7)

    @property
    def total(self) -> int:
        return sum(self.seconds)


@dataclass
class Week:
    start: date
    rows: list[Row]

    @property
    def days(self) -> list[date]:
        return [self.start + timedelta(days=i) for i in range(7)]

    @property
    def totals(self) -> list[int]:
        return [sum(r.seconds[i] for r in self.rows) for i in range(7)]


def entries_in_week(db: Session, user: User, start: date) -> list[TimeEntry]:
    begin = datetime.combine(start, time.min, tzinfo=UTC)
    end = begin + timedelta(days=7)
    stmt = (
        select(TimeEntry)
        .options(joinedload(TimeEntry.project).joinedload(Project.client))
        .where(
            TimeEntry.user_id == user.id,
            TimeEntry.started_at >= begin,
            TimeEntry.started_at < end,
        )
        .order_by(TimeEntry.started_at)
    )
    return list(db.scalars(stmt))


def build_week(db: Session, user: User, day: date) -> Week:
    start = week_start(day)
    rows: dict[int, Row] = {}
    for entry in entries_in_week(db, user, start):
        row = rows.setdefault(entry.project_id, Row(entry.project))
        index = (entry.started_at.date() - start).days
        row.seconds[index] += entry.duration_seconds
    ordered = sorted(rows.values(), key=lambda r: (r.project.client.name, r.project.name))
    return Week(start=start, rows=ordered)


class CellError(ValueError):
    pass


def set_cell(db: Session, user: User, project: Project, day: date, seconds: int) -> None:
    """Make the project's total for `day` equal `seconds`.

    Timer and manual entries are left alone; the difference is kept in a single
    "grid" entry for the cell that is created, resized or removed as needed.
    """
    begin = datetime.combine(day, time.min, tzinfo=UTC)
    stmt = select(TimeEntry).where(
        TimeEntry.user_id == user.id,
        TimeEntry.project_id == project.id,
        TimeEntry.started_at >= begin,
        TimeEntry.started_at < begin + timedelta(days=1),
    )
    entries = list(db.scalars(stmt))
    grid = [e for e in entries if e.source == "grid"]
    fixed = sum(e.duration_seconds for e in entries if e.source != "grid")
    if seconds < fixed:
        raise CellError(
            f"This day already has {fixed // 60} min of tracked time; "
            "edit those entries to go lower"
        )
    for entry in grid:
        db.delete(entry)
    remainder = seconds - fixed
    if remainder > 0:
        start = begin + timedelta(hours=9)
        db.add(
            TimeEntry(
                user_id=user.id,
                project_id=project.id,
                started_at=start,
                ended_at=start + timedelta(seconds=remainder),
                billable=project.billable,
                source="grid",
            )
        )
    db.commit()
