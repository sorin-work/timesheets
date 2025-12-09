"""Billing increments. Freelancers usually bill in 6 minute (1/10 h) or 15 minute steps."""

from enum import StrEnum


class Rounding(StrEnum):
    NONE = "none"
    SIX = "6"
    FIFTEEN = "15"

    @property
    def step_seconds(self) -> int:
        return 0 if self is Rounding.NONE else int(self.value) * 60


def round_seconds(seconds: int, rule: Rounding | str) -> int:
    """Round a duration up to the next billing increment."""
    rule = Rounding(rule)
    if seconds <= 0:
        return 0
    if rule is Rounding.NONE:
        return seconds
    step = rule.step_seconds
    return (seconds // step + 1) * step


def billable_hours(seconds: int, rule: Rounding | str) -> float:
    return round_seconds(seconds, rule) / 3600
