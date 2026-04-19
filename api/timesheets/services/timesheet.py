"""Weekly timesheet: seconds per project per day, Monday to Sunday."""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

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


def _local_midnight(day: date, tz: ZoneInfo) -> datetime:
    return datetime.combine(day, time.min, tzinfo=tz)


def entries_in_week(db: Session, user: User, start: date) -> list[TimeEntry]:
    tz = ZoneInfo(user.timezone)
    begin = _local_midnight(start, tz)
    end = _local_midnight(start + timedelta(days=7), tz)
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
    tz = ZoneInfo(user.timezone)
    rows: dict[int, Row] = {}
    for entry in entries_in_week(db, user, start):
        row = rows.setdefault(entry.project_id, Row(entry.project))
        # Entries belong to the day they started on in the user's time zone.
        index = (entry.started_at.astimezone(tz).date() - start).days
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
    tz = ZoneInfo(user.timezone)
    begin = _local_midnight(day, tz)
    stmt = select(TimeEntry).where(
        TimeEntry.user_id == user.id,
        TimeEntry.project_id == project.id,
        TimeEntry.started_at >= begin,
        TimeEntry.started_at < _local_midnight(day + timedelta(days=1), tz),
    )
    entries = list(db.scalars(stmt))
    # Invoiced grid entries are as fixed as tracked ones.
    grid = [e for e in entries if e.source == "grid" and e.invoice_id is None]
    fixed = sum(e.duration_seconds for e in entries if e not in grid)
    if seconds < fixed:
        raise CellError(
            f"This day already has {fixed // 60} min of tracked time; "
            "edit or unbill those entries to go lower"
        )
    for entry in grid:
        db.delete(entry)
    remainder = seconds - fixed
    if remainder > 0:
        start = datetime.combine(day, time(9), tzinfo=tz)
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
