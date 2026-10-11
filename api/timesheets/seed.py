"""Demo data: `python -m timesheets.seed` creates demo@example.com / demo-password.

Six months of realistic weekday time across three clients, with invoices in every
state. Safe to run repeatedly: does nothing when the demo user already exists.
"""

import argparse
import random
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from timesheets import clock, db
from timesheets.models import Client, Project, TimeEntry, User
from timesheets.security import hash_password
from timesheets.services.invoicing import GenerateOptions, change_status, generate_invoice

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo-password"

CLIENTS = [
    {
        "name": "Northwind Traders",
        "email": "accounts@northwind.example",
        "address": "12 Harbour Road\nBristol BS1 4QA\nUnited Kingdom",
        "currency": "GBP",
        "hourly_rate": Decimal("75.00"),
        "projects": [
            ("Website redesign", None, True, "#4f46e5"),
            ("Support retainer", Decimal("60.00"), True, "#0891b2"),
        ],
    },
    {
        "name": "Blue Fjord AS",
        "email": "faktura@bluefjord.example",
        "address": "Strandgata 5\n5013 Bergen\nNorway",
        "currency": "EUR",
        "hourly_rate": Decimal("90.00"),
        "projects": [
            ("Booking app", None, True, "#059669", Decimal("100")),
            ("Code review", Decimal("110.00"), True, "#ca8a04"),
        ],
    },
    {
        "name": "Atelier Lumière",
        "email": "bonjour@lumiere.example",
        "address": "8 rue des Arts\n69002 Lyon\nFrance",
        "currency": "EUR",
        "hourly_rate": Decimal("65.00"),
        "projects": [("Shop maintenance", None, True, "#db2777")],
    },
]

TASKS = [
    "Planning call",
    "Implement filters",
    "Fix checkout bug",
    "Code review",
    "Deploy and smoke test",
    "Write tests",
    "Design tweaks",
    "Performance profiling",
    "Email and admin",
    "Refactor API client",
    "Update dependencies",
    "Investigate support ticket",
]


def _demo_user(session: Session) -> User:
    user = User(
        email=DEMO_EMAIL,
        name="Dana Demo",
        password_hash=hash_password(DEMO_PASSWORD),
        timezone="Europe/London",
        rounding="6",
        currency="EUR",
        business_name="Dana Demo Development",
        business_address="Flat 3, 41 Elm Street\nManchester M1 2AB\nUnited Kingdom",
        tax_id="GB123456789",
        payment_details=(
            "Example Bank · Sort code 04-00-04 · Account 12345678\nIBAN GB33 EXMP 0400 0412 3456 78"
        ),
        invoice_prefix="DD-",
        payment_terms_days=14,
        weekly_target_hours=Decimal("30"),
    )
    session.add(user)
    session.flush()
    return user


def _projects(session: Session, user: User) -> list[Project]:
    projects = []
    for spec in CLIENTS:
        data = {k: v for k, v in spec.items() if k != "projects"}
        client = Client(user_id=user.id, **data)
        session.add(client)
        for name, rate, billable, color, *budget in spec["projects"]:
            project = Project(
                user_id=user.id,
                client=client,
                name=name,
                hourly_rate=rate,
                billable=billable,
                color=color,
                budget_hours=budget[0] if budget else None,
            )
            session.add(project)
            projects.append(project)
    internal = Client(user_id=user.id, name="Internal", currency="EUR")
    admin = Project(user_id=user.id, client=internal, name="Admin", billable=False, color="#475569")
    session.add_all([internal, admin])
    projects.append(admin)
    session.flush()
    return projects


def _entries(session: Session, user: User, projects: list[Project], days: int, rng: random.Random):
    now = clock.now()
    today = now.date()
    start_day = today - timedelta(days=days)
    for offset in range(days + 1):
        day = start_day + timedelta(days=offset)
        if day.weekday() >= 5 and rng.random() > 0.1:
            continue
        cursor = datetime.combine(day, time(8, rng.choice([0, 15, 30])), tzinfo=UTC)
        for _ in range(rng.randint(2, 4)):
            project = rng.choice(projects)
            minutes = rng.choice([25, 40, 50, 65, 80, 95, 120, 150])
            end = cursor + timedelta(minutes=minutes)
            if end > now:
                break
            session.add(
                TimeEntry(
                    user_id=user.id,
                    project_id=project.id,
                    started_at=cursor,
                    ended_at=end,
                    description=rng.choice(TASKS),
                    billable=project.billable,
                    source=rng.choice(["timer", "timer", "manual"]),
                )
            )
            cursor = end + timedelta(minutes=rng.choice([5, 15, 30, 60]))
    session.flush()


def _invoices(session: Session, user: User, months: int) -> None:
    """Invoice each finished month per client: older ones paid, the last one sent."""
    today = clock.today()
    first_this_month = today.replace(day=1)
    clients = session.scalars(
        select(Client).where(Client.user_id == user.id, Client.name != "Internal")
    ).all()
    for back in range(months, 0, -1):
        period_end = first_this_month
        for _ in range(back - 1):
            period_end = (period_end - timedelta(days=1)).replace(day=1)
        period_end -= timedelta(days=1)
        period_start = period_end.replace(day=1)
        issue = period_end + timedelta(days=2)
        for client in clients:
            try:
                invoice = generate_invoice(
                    session,
                    user,
                    client,
                    GenerateOptions(
                        client_id=client.id,
                        period_start=period_start,
                        period_end=period_end,
                        issue_date=issue,
                        taxes=[("VAT", Decimal("20"))] if client.currency == "GBP" else [],
                        notes="Thank you for your business!\nBank transfer within 14 days.",
                    ),
                )
            except Exception:  # nothing to bill for that client and month
                session.rollback()
                continue
            change_status(session, invoice, "send", datetime.combine(issue, time(10), tzinfo=UTC))
            if back > 1 or client.currency == "GBP":
                paid_on = issue + timedelta(days=9 if back > 1 else 4)
                if paid_on < today:
                    change_status(
                        session, invoice, "pay", datetime.combine(paid_on, time(15), tzinfo=UTC)
                    )


def seed(session: Session, days: int = 180) -> User | None:
    if session.scalar(select(User).where(User.email == DEMO_EMAIL)) is not None:
        return None
    rng = random.Random(4412)
    user = _demo_user(session)
    projects = _projects(session, user)
    _entries(session, user, projects, days, rng)
    session.commit()
    _invoices(session, user, months=min(5, days // 31))
    _draft_for_this_month(session, user)
    session.commit()
    return user


def _draft_for_this_month(session: Session, user: User) -> None:
    """The current month so far for the biggest client, still a draft."""
    today = clock.today()
    client = session.scalar(
        select(Client).where(Client.user_id == user.id, Client.name == "Blue Fjord AS")
    )
    if client is None or today.day == 1:
        return
    try:
        generate_invoice(
            session,
            user,
            client,
            GenerateOptions(
                client_id=client.id,
                period_start=today.replace(day=1),
                period_end=today - timedelta(days=1),
                issue_date=today,
                reference="PO-2026-118",
            ),
        )
    except Exception:  # nothing tracked yet this month
        session.rollback()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=180, help="days of history to create")
    args = parser.parse_args()
    with db.session_factory()() as session:
        user = seed(session, days=args.days)
    if user is None:
        print(f"{DEMO_EMAIL} already exists, nothing to do")
    else:
        print(f"Created {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
