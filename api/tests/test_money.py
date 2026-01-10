from decimal import Decimal

import pytest

from timesheets.services.money import format_money, hours_from_seconds, line_amount, to_money


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1.005", "1.01"), ("2.675", "2.68"), ("10", "10.00"), ("-1.005", "-1.01"), (3, "3.00")],
)
def test_to_money_rounds_half_up(value, expected):
    assert to_money(value) == Decimal(expected)


def test_hours_from_seconds():
    assert hours_from_seconds(5400) == Decimal("1.50")
    assert hours_from_seconds(360) == Decimal("0.10")
    assert hours_from_seconds(100) == Decimal("0.03")


def test_line_amount():
    assert line_amount(Decimal("1.50"), Decimal("85.00")) == Decimal("127.50")
    assert line_amount(Decimal("0.10"), Decimal("33.33")) == Decimal("3.33")
    assert line_amount(Decimal("0.25"), Decimal("90.10")) == Decimal("22.53")


def test_format_money():
    assert format_money(Decimal("1234.5"), "EUR") == "1,234.50 EUR"
    assert format_money(Decimal("-3"), "USD") == "-3.00 USD"
