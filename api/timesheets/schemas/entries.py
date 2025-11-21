from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

MAX_ENTRY = timedelta(hours=24)

Description = Annotated[str, Field(max_length=500)]


class EntryIn(BaseModel):
    project_id: int
    started_at: AwareDatetime
    ended_at: AwareDatetime
    description: Description = ""
    billable: bool | None = None  # defaults to the project's setting

    @model_validator(mode="after")
    def check_range(self) -> Self:
        if self.ended_at <= self.started_at:
            raise ValueError("ended_at must be after started_at")
        if self.ended_at - self.started_at > MAX_ENTRY:
            raise ValueError("a single entry cannot be longer than 24 hours")
        self.description = self.description.strip()
        return self


class EntryUpdate(BaseModel):
    project_id: int | None = None
    started_at: AwareDatetime | None = None
    ended_at: AwareDatetime | None = None
    description: Description | None = None
    billable: bool | None = None

    @model_validator(mode="after")
    def check_range(self) -> Self:
        if self.started_at and self.ended_at:
            if self.ended_at <= self.started_at:
                raise ValueError("ended_at must be after started_at")
            if self.ended_at - self.started_at > MAX_ENTRY:
                raise ValueError("a single entry cannot be longer than 24 hours")
        if self.description is not None:
            self.description = self.description.strip()
        return self


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    project_name: str
    client_id: int
    client_name: str
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    running: bool
    description: str
    billable: bool
    source: str
    hourly_rate: Decimal | None


class EntryPage(BaseModel):
    items: list[EntryOut]
    total: int
    page: int
    page_size: int
    pages: int
