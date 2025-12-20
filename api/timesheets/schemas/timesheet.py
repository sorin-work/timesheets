from datetime import date

from pydantic import BaseModel


class TimesheetRow(BaseModel):
    project_id: int
    project_name: str
    client_name: str
    color: str
    seconds: list[int]
    total: int


class TimesheetOut(BaseModel):
    week_start: date
    days: list[date]
    rows: list[TimesheetRow]
    totals: list[int]
    total: int
