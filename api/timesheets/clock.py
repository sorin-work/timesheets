"""Single place to ask for the current time, so tests can pin it."""

from datetime import UTC, date, datetime


def now() -> datetime:
    return datetime.now(UTC)


def today() -> date:
    return now().date()
