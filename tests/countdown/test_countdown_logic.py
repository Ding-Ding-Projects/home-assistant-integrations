from datetime import date

from conftest import load_logic

L = load_logic("countdown")


def test_yearly_later_this_year():
    assert L.next_occurrence(date(1990, 8, 20), True, date(2026, 3, 1)) == date(2026, 8, 20)


def test_yearly_already_passed_rolls_to_next_year():
    assert L.next_occurrence(date(1990, 2, 1), True, date(2026, 3, 1)) == date(2027, 2, 1)


def test_yearly_today_is_zero_days():
    assert L.days_until(date(1990, 3, 1), True, date(2026, 3, 1)) == 0


def test_leap_day_in_non_leap_year():
    assert L.next_occurrence(date(2000, 2, 29), True, date(2026, 1, 1)) == date(2026, 2, 28)
    assert L.next_occurrence(date(2000, 2, 29), True, date(2027, 3, 1)) == date(2028, 2, 29)


def test_one_off_future_and_past():
    assert L.days_until(date(2026, 12, 25), False, date(2026, 12, 1)) == 24
    assert L.days_until(date(2026, 1, 1), False, date(2026, 12, 1)) is None
    assert L.next_occurrence(date(2026, 1, 1), False, date(2026, 12, 1)) is None


def test_years_marked():
    assert L.years_marked(date(1990, 8, 20), date(2026, 3, 1)) == 36
    assert L.years_marked(date(1990, 2, 1), date(2026, 3, 1)) == 37
