from datetime import date

import pytest

pytest.importorskip("astral")

from conftest import load_logic  # noqa: E402

L = load_logic("sun_hours")
TORONTO = (43.65, -79.38)


def test_summer_solstice_is_long():
    minutes = L.daylight_minutes(*TORONTO, date(2026, 6, 21))
    assert 925 < minutes < 935  # about 15h 28m


def test_winter_solstice_is_short():
    minutes = L.daylight_minutes(*TORONTO, date(2026, 12, 21))
    assert 535 < minutes < 545  # about 9h 0m


def test_change_sign_follows_season():
    assert L.change_vs_yesterday(*TORONTO, date(2026, 3, 20)) > 0
    assert L.change_vs_yesterday(*TORONTO, date(2026, 9, 25)) < 0


def test_equator_is_about_twelve_hours():
    assert 715 < L.daylight_minutes(0.0, 0.0, date(2026, 3, 20)) < 735


def test_polar_day_and_night():
    assert L.daylight_minutes(78.0, 15.0, date(2026, 6, 21)) == 1440.0
    assert L.daylight_minutes(78.0, 15.0, date(2026, 12, 21)) == 0.0
