import pytest

from timesheets.services.rounding import Rounding, billable_hours, round_seconds


def test_no_rounding_keeps_seconds():
    assert round_seconds(61, Rounding.NONE) == 61
    assert round_seconds(61, "none") == 61


@pytest.mark.parametrize(
    ("seconds", "expected_minutes"),
    [(1, 6), (5 * 60, 6), (7 * 60, 12), (61 * 60, 66), (89 * 60 + 59, 90)],
)
def test_six_minute_rounding_rounds_up(seconds, expected_minutes):
    assert round_seconds(seconds, Rounding.SIX) == expected_minutes * 60


@pytest.mark.parametrize(
    ("seconds", "expected_minutes"),
    [(1, 15), (14 * 60, 15), (16 * 60, 30), (50 * 60, 60)],
)
def test_quarter_hour_rounding_rounds_up(seconds, expected_minutes):
    assert round_seconds(seconds, "15") == expected_minutes * 60


def test_zero_and_negative_durations_round_to_zero():
    assert round_seconds(0, Rounding.FIFTEEN) == 0
    assert round_seconds(-30, Rounding.SIX) == 0


def test_billable_hours():
    assert billable_hours(20 * 60, Rounding.FIFTEEN) == 0.5


def test_unknown_rule_is_rejected():
    with pytest.raises(ValueError):
        round_seconds(60, "10")
