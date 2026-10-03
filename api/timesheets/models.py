"""Database models. Imported by Alembic so every table is registered on Base.metadata."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from timesheets import clock
from timesheets.db import Base, TimestampMixin

Money = Numeric(12, 2)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))

    # Preferences
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC")
    rounding: Mapped[str] = mapped_column(String(4), default="none", server_default="none")
    currency: Mapped[str] = mapped_column(String(3), default="EUR", server_default="EUR")
    weekly_target_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    # Shown on invoices
    business_name: Mapped[str | None] = mapped_column(String(200))
    business_address: Mapped[str | None] = mapped_column(Text)
    tax_id: Mapped[str | None] = mapped_column(String(64))
    # Bank account, IBAN, PayPal... printed at the bottom of every invoice
    payment_details: Mapped[str | None] = mapped_column(Text)
    invoice_prefix: Mapped[str] = mapped_column(String(16), default="INV-", server_default="INV-")
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=14, server_default="14")
    # [{"name": "VAT", "rate": "19"}], used when an invoice is generated without taxes
    default_taxes: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )


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
    budget_hours: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()
    client: Mapped[Client] = relationship()

    @property
    def effective_rate(self) -> Decimal | None:
        if self.hourly_rate is not None:
            return self.hourly_rate
        return self.client.hourly_rate

    # Filled in by the projects router from an aggregate query.
    used_seconds: int = 0

    @property
    def client_name(self) -> str:
        return self.client.name

    @property
    def currency(self) -> str:
        return self.client.currency


class TimeEntry(TimestampMixin, Base):
    __tablename__ = "time_entries"
    __table_args__ = (
        Index("ix_time_entries_user_started", "user_id", "started_at"),
        # Unbilled time lookups (dashboard, invoice preview and generation)
        Index(
            "ix_time_entries_unbilled",
            "user_id",
            "project_id",
            postgresql_where=text("invoice_id IS NULL AND billable"),
        ),
        # At most one running timer per user.
        Index(
            "uq_time_entries_one_running",
            "user_id",
            unique=True,
            postgresql_where=text("ended_at IS NULL"),
        ),
    )

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
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id", ondelete="SET NULL"), index=True
    )

    user: Mapped[User] = relationship()
    project: Mapped[Project] = relationship()

    @property
    def project_name(self) -> str:
        return self.project.name

    @property
    def client_id(self) -> int:
        return self.project.client_id

    @property
    def client_name(self) -> str:
        return self.project.client.name

    @property
    def hourly_rate(self) -> Decimal | None:
        return self.project.effective_rate

    @property
    def running(self) -> bool:
        return self.ended_at is None

    @property
    def duration_seconds(self) -> int:
        end = self.ended_at or datetime.now(UTC)
        return int((end - self.started_at).total_seconds())


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("user_id", "number", name="uq_invoices_user_number"),
        Index("ix_invoices_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"), index=True
    )
    number: Mapped[str] = mapped_column(String(32))
    sequence: Mapped[int] = mapped_column(Integer)
    # draft -> sent -> paid. "overdue" is derived from sent + due date.
    status: Mapped[str] = mapped_column(String(10), default="draft")
    issue_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3))
    # The client's purchase order or reference, if they need one on the invoice
    reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    subtotal: Mapped[Decimal] = mapped_column(Money, default=Decimal("0.00"))
    tax_total: Mapped[Decimal] = mapped_column(Money, default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Money, default=Decimal("0.00"))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    client: Mapped[Client] = relationship()
    lines: Mapped[list["InvoiceLine"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", order_by="InvoiceLine.position"
    )
    taxes: Mapped[list["InvoiceTax"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", order_by="InvoiceTax.id"
    )
    entries: Mapped[list[TimeEntry]] = relationship()

    @property
    def client_name(self) -> str:
        return self.client.name

    @property
    def is_overdue(self) -> bool:
        # Payment is due *on* the due date; it is late from the day after.
        return self.status == "sent" and self.due_date < clock.today()

    @property
    def display_status(self) -> str:
        """draft, sent, paid, or overdue for sent invoices past their due date."""
        return "overdue" if self.is_overdue else self.status

    @property
    def entry_count(self) -> int:
        # A count query instead of loading every entry of a long invoice.
        session = object_session(self)
        if session is None:
            return len(self.entries)
        return session.scalar(
            select(func.count()).select_from(TimeEntry).where(TimeEntry.invoice_id == self.id)
        )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    unit_price: Mapped[Decimal] = mapped_column(Money)
    amount: Mapped[Decimal] = mapped_column(Money)

    invoice: Mapped[Invoice] = relationship(back_populates="lines")


class InvoiceTax(Base):
    __tablename__ = "invoice_taxes"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(60))
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    amount: Mapped[Decimal] = mapped_column(Money, default=Decimal("0.00"))

    invoice: Mapped[Invoice] = relationship(back_populates="taxes")
