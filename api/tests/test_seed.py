from sqlalchemy import func, select

from timesheets.models import Invoice, TimeEntry
from timesheets.seed import DEMO_EMAIL, DEMO_PASSWORD, seed


def test_seed_creates_a_usable_demo_account(session, client):
    user = seed(session, days=100)
    assert user is not None
    assert session.scalar(select(func.count()).select_from(TimeEntry)) > 100
    statuses = set(session.scalars(select(Invoice.status)))
    assert {"paid", "sent"} <= statuses

    r = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200


def test_seed_is_idempotent(session):
    assert seed(session, days=10) is not None
    assert seed(session, days=10) is None
