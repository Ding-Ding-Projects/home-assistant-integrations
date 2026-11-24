from datetime import date, datetime

import pytest

from conftest import load_logic

L = load_logic("bin_day")
START = date(2026, 1, 5)  # a Monday


def test_start_date_in_future_is_next():
    assert L.next_collection(START, 1, date(2025, 12, 1)) == START


def test_collection_today_counts():
    assert L.next_collection(START, 2, date(2026, 1, 19)) == date(2026, 1, 19)
    assert L.days_until(START, 2, date(2026, 1, 19)) == 0


@pytest.mark.parametrize(
    "today,expected",
    [
        (date(2026, 1, 6), date(2026, 1, 19)),
        (date(2026, 1, 20), date(2026, 2, 2)),
        (date(2026, 12, 31), date(2027, 1, 4)),
    ],
)
def test_fortnightly(today, expected):
    assert L.next_collection(START, 2, today) == expected


def test_weekly_days_until():
    assert L.days_until(START, 1, date(2026, 1, 9)) == 3


def test_invalid_interval():
    with pytest.raises(ValueError):
        L.next_collection(START, 0, date(2026, 1, 6))


def test_put_bins_out_evening_before():
    # collection Monday 2026-01-19; the evening before is Sunday the 18th
    assert not L.put_bins_out(datetime(2026, 1, 18, 16, 59), START, 2)
    assert L.put_bins_out(datetime(2026, 1, 18, 17, 0), START, 2)
    assert L.put_bins_out(datetime(2026, 1, 19, 6, 0), START, 2)


def test_put_bins_out_off_between_rounds():
    assert not L.put_bins_out(datetime(2026, 1, 12, 20, 0), START, 2)


def test_custom_evening_hour():
    assert L.put_bins_out(datetime(2026, 1, 18, 8, 0), START, 2, evening_hour=7)
