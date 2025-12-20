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
