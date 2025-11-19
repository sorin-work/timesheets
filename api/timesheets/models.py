"""Database models. Imported by Alembic so every table is registered on Base.metadata."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from timesheets.db import Base, TimestampMixin

Money = Numeric(12, 2)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))


class Client(TimestampMixin, Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(254))
    address: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    hourly_rate: Mapped[Decimal | None] = mapped_column(Money)
    notes: Mapped[str | None] = mapped_column(Text)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    # When empty the client's rate applies.
    hourly_rate: Mapped[Decimal | None] = mapped_column(Money)
    billable: Mapped[bool] = mapped_column(Boolean, default=True)
    color: Mapped[str] = mapped_column(String(7), default="#4f46e5")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()
    client: Mapped[Client] = relationship()

    @property
    def effective_rate(self) -> Decimal | None:
        if self.hourly_rate is not None:
            return self.hourly_rate
        return self.client.hourly_rate

    @property
    def client_name(self) -> str:
        return self.client.name

    @property
    def currency(self) -> str:
        return self.client.currency


class TimeEntry(TimestampMixin, Base):
    __tablename__ = "time_entries"
    __table_args__ = (Index("ix_time_entries_user_started", "user_id", "started_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # NULL while the timer is running.
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    description: Mapped[str] = mapped_column(String(500), default="")
    billable: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(10), default="manual")

    user: Mapped[User] = relationship()
    project: Mapped[Project] = relationship()

    @property
    def running(self) -> bool:
        return self.ended_at is None

    @property
    def duration_seconds(self) -> int:
        end = self.ended_at or datetime.now(UTC)
        return int((end - self.started_at).total_seconds())
