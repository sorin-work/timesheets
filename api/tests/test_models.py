import pytest
from sqlalchemy.exc import IntegrityError

from timesheets.models import User


def test_user_timestamps_are_set_by_the_database(session):
    user = User(email="ana@example.com", password_hash="x", name="Ana")
    session.add(user)
    session.commit()
    session.refresh(user)
    assert user.id == 1
    assert user.created_at is not None
    assert user.created_at.tzinfo is not None


def test_user_email_is_unique(session):
    session.add(User(email="ana@example.com", password_hash="x", name="Ana"))
    session.commit()
    session.add(User(email="ana@example.com", password_hash="y", name="Other"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_project_rate_falls_back_to_the_client_rate(session):
    from decimal import Decimal

    from timesheets.models import Client, Project

    user = User(email="ana@example.com", password_hash="x", name="Ana")
    client = Client(user=user, name="Acme", hourly_rate=Decimal("80.00"))
    own_rate = Project(user=user, client=client, name="Audit", hourly_rate=Decimal("120.00"))
    inherited = Project(user=user, client=client, name="Support")
    session.add_all([own_rate, inherited])
    session.commit()
    assert own_rate.effective_rate == Decimal("120.00")
    assert inherited.effective_rate == Decimal("80.00")
    assert inherited.billable is True
