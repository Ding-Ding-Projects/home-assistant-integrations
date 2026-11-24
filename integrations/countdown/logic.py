"""Pure date-countdown logic for Countdown (no Home Assistant imports)."""

from __future__ import annotations

import calendar
from datetime import date


def _safe_date(year: int, month: int, day: int) -> date:
    """Build a date, moving 29 February to 28 February in non-leap years."""
    if month == 2 and day == 29 and not calendar.isleap(year):
        day = 28
    return date(year, month, day)


def next_occurrence(target: date, yearly: bool, today: date) -> date | None:
    """Return the next date on or after today, or None for a past one-off."""
    if not yearly:
        return target if target >= today else None
    candidate = _safe_date(today.year, target.month, target.day)
    if candidate < today:
        candidate = _safe_date(today.year + 1, target.month, target.day)
    return candidate


def days_until(target: date, yearly: bool, today: date) -> int | None:
    """Return whole days until the next occurrence, or None if there is none."""
    nxt = next_occurrence(target, yearly, today)
    return None if nxt is None else (nxt - today).days


def years_marked(target: date, today: date) -> int | None:
    """Return how many years the next yearly occurrence marks (age or anniversary)."""
    nxt = next_occurrence(target, True, today)
    return None if nxt is None else nxt.year - target.year
