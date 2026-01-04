from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import ValidationFailed
from timesheets.models import Project
from timesheets.routers.entries import _active_project
from timesheets.schemas.timesheet import TimesheetOut, TimesheetRow
from timesheets.services.timesheet import CellError, build_week, set_cell

router = APIRouter(prefix="/api/timesheet", tags=["timesheet"])


class CellIn(BaseModel):
    project_id: int
    date: date
    minutes: int = Field(ge=0, le=24 * 60)


@router.get("", response_model=TimesheetOut)
def get_week(
    db: DbSession,
    user: CurrentUser,
    week: Annotated[date | None, Query(description="Any day in the week")] = None,
) -> TimesheetOut:
    return _serialize(db, user, week or date.today())


@router.put("/cell", response_model=TimesheetOut)
def put_cell(body: CellIn, db: DbSession, user: CurrentUser) -> TimesheetOut:
    """Set the total time for one project on one day; returns the updated week."""
    project: Project = _active_project(db, body.project_id, user)
    try:
        set_cell(db, user, project, body.date, body.minutes * 60)
    except CellError as exc:
        raise ValidationFailed(str(exc)) from exc
    return _serialize(db, user, body.date)


def _serialize(db, user, day: date) -> TimesheetOut:
    sheet = build_week(db, user, day)
    return TimesheetOut(
        week_start=sheet.start,
        days=sheet.days,
        rows=[
            TimesheetRow(
                project_id=row.project.id,
                project_name=row.project.name,
                client_name=row.project.client.name,
                color=row.project.color,
                seconds=row.seconds,
                total=row.total,
            )
            for row in sheet.rows
        ],
        totals=sheet.totals,
        total=sum(sheet.totals),
    )
