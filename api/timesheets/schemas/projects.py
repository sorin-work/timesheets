from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from timesheets.schemas.common import Name, Rate

Color = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]
Budget = Annotated[Decimal, Field(gt=0, le=100000, max_digits=8, decimal_places=2)]


class ProjectIn(BaseModel):
    client_id: int
    name: Name
    hourly_rate: Rate | None = None
    billable: bool = True
    color: Color = "#4f46e5"
    budget_hours: Budget | None = None


class ProjectUpdate(BaseModel):
    name: Name | None = None
    hourly_rate: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    billable: bool | None = None
    color: Color | None = None
    budget_hours: Budget | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    client_name: str
    name: str
    hourly_rate: Decimal | None
    effective_rate: Decimal | None
    currency: str
    billable: bool
    color: str
    budget_hours: Decimal | None
    used_seconds: int
    archived_at: datetime | None
    created_at: datetime
