"""Pure collection-schedule logic for Bin Day (no Home Assistant imports)."""

from __future__ import annotations

from datetime import date, datetime, timedelta


def next_collection(start: date, interval_weeks: int, today: date) -> date:
    """Return the first collection on or after today.

    Collections happen on start, then every interval_weeks weeks after it.
    """
    if interval_weeks < 1:
        raise ValueError("interval_weeks must be at least 1")
    if today <= start:
        return start
    step = 7 * interval_weeks
    elapsed = (today - start).days
    periods = -(-elapsed // step)  # ceiling division
    return start + timedelta(days=periods * step)


def days_until(start: date, interval_weeks: int, today: date) -> int:
    """Return whole days from today until the next collection."""
    return (next_collection(start, interval_weeks, today) - today).days


def put_bins_out(
    now: datetime, start: date, interval_weeks: int, evening_hour: int = 17
) -> bool:
    """Return True from the evening before a collection until collection day ends."""
    today = now.date()
    due = next_collection(start, interval_weeks, today)
    if due == today:
        return True
    return due == today + timedelta(days=1) and now.hour >= evening_hour
