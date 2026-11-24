"""Pure seed-starting stage logic for Seed Tray (no Home Assistant imports)."""

from __future__ import annotations

from datetime import date, timedelta

STAGE_PLANNED = "planned"
STAGE_GERMINATING = "germinating"
STAGE_GROWING = "growing"
STAGE_READY = "ready_to_transplant"


def validate(germination_days: int, transplant_days: int) -> None:
    """Raise ValueError if the schedule is not usable."""
    if germination_days < 1:
        raise ValueError("germination_days must be at least 1")
    if transplant_days <= germination_days:
        raise ValueError("transplant_days must be greater than germination_days")


def stage(sow: date, germination_days: int, transplant_days: int, today: date) -> str:
    """Return the tray stage on the given day."""
    validate(germination_days, transplant_days)
    age = (today - sow).days
    if age < 0:
        return STAGE_PLANNED
    if age < germination_days:
        return STAGE_GERMINATING
    if age < transplant_days:
        return STAGE_GROWING
    return STAGE_READY


def germination_date(sow: date, germination_days: int) -> date:
    return sow + timedelta(days=germination_days)


def transplant_date(sow: date, transplant_days: int) -> date:
    return sow + timedelta(days=transplant_days)


def days_to_transplant(sow: date, transplant_days: int, today: date) -> int:
    """Return days until transplant, never below zero."""
    return max(0, (transplant_date(sow, transplant_days) - today).days)
