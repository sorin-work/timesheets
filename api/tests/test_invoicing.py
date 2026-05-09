from datetime import date

from timesheets.models import Client, Invoice, User
from timesheets.services.invoicing import next_number


def make_user(session, email="ana@example.com", prefix="INV-"):
    user = User(email=email, password_hash="x", name="Ana", invoice_prefix=prefix)
    session.add(user)
    session.flush()
    return user


def add_invoice(session, user, sequence):
    client = Client(user=user, name="Acme")
    session.add(
        Invoice(
            user_id=user.id,
            client=client,
            number=f"X{sequence}",
            sequence=sequence,
            issue_date=date(2026, 1, 1),
            due_date=date(2026, 1, 15),
            currency="EUR",
        )
    )
    session.flush()


def test_first_invoice_number(session):
    user = make_user(session)
    assert next_number(session, user) == (1, "INV-1")


def test_numbers_continue_per_user(session):
    ana = make_user(session)
    bob = make_user(session, "bob@example.com", prefix="B/")
    add_invoice(session, ana, 1)
    add_invoice(session, ana, 2)
    assert next_number(session, ana) == (3, "INV-3")
    assert next_number(session, bob) == (1, "B/1")


def test_tax_amount():
    from decimal import Decimal

    from timesheets.services.invoicing import tax_amount

    assert tax_amount(Decimal("300.00"), Decimal("19")) == Decimal("57.00")
    assert tax_amount(Decimal("99.99"), Decimal("21")) == Decimal("21.00")
    assert tax_amount(Decimal("0.00"), Decimal("19")) == Decimal("0.00")


def test_tax_amount_rounds_half_cents_up():
    from decimal import Decimal

    from timesheets.services.invoicing import tax_amount

    assert tax_amount(Decimal("50.50"), Decimal("9")) == Decimal("4.55")
    assert tax_amount(Decimal("12.50"), Decimal("5")) == Decimal("0.63")
    assert tax_amount(Decimal("102.50"), Decimal("19")) == Decimal("19.48")
