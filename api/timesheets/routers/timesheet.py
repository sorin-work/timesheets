from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from timesheets.deps import CurrentUser, DbSession
from timesheets.schemas.timesheet import TimesheetOut, TimesheetRow
from timesheets.services.timesheet import build_week

router = APIRouter(prefix="/api/timesheet", tags=["timesheet"])


@router.get("", response_model=TimesheetOut)
def get_week(
    db: DbSession,
    user: CurrentUser,
    week: Annotated[date | None, Query(description="Any day in the week")] = None,
) -> TimesheetOut:
    sheet = build_week(db, user, week or date.today())
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
