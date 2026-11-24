"""Daylight computation for Sun Hours (uses astral, a Home Assistant dependency)."""

from __future__ import annotations

from datetime import date, timedelta, tzinfo

from astral import Observer
from astral.sun import daylight, elevation, noon

POLAR_THRESHOLD_DEGREES = -0.833


def daylight_minutes(
    latitude: float, longitude: float, day: date, tz: tzinfo | None = None
) -> float:
    """Return minutes between sunrise and sunset on a day.

    Polar day returns 1440 and polar night returns 0.
    """
    observer = Observer(latitude, longitude)
    kwargs = {"tzinfo": tz} if tz else {}
    try:
        sunrise, sunset = daylight(observer, day, **kwargs)
    except ValueError:
        solar_noon = noon(observer, day, **kwargs)
        up = elevation(observer, solar_noon) > POLAR_THRESHOLD_DEGREES
        return 1440.0 if up else 0.0
    return round((sunset - sunrise).total_seconds() / 60, 1)


def change_vs_yesterday(
    latitude: float, longitude: float, day: date, tz: tzinfo | None = None
) -> float:
    """Return today's daylight minus yesterday's, in minutes."""
    today = daylight_minutes(latitude, longitude, day, tz)
    yesterday = daylight_minutes(latitude, longitude, day - timedelta(days=1), tz)
    return round(today - yesterday, 1)
