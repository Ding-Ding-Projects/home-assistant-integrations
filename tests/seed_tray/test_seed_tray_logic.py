from datetime import date

import pytest

from conftest import load_logic

L = load_logic("seed_tray")
SOW = date(2026, 3, 1)


@pytest.mark.parametrize(
    "today,expected",
    [
        (date(2026, 2, 28), "planned"),
        (date(2026, 3, 1), "germinating"),
        (date(2026, 3, 7), "germinating"),
        (date(2026, 3, 8), "growing"),
        (date(2026, 3, 28), "growing"),
        (date(2026, 3, 29), "ready_to_transplant"),
        (date(2026, 6, 1), "ready_to_transplant"),
    ],
)
def test_stage(today, expected):
    assert L.stage(SOW, 7, 28, today) == expected


def test_days_to_transplant_never_negative():
    assert L.days_to_transplant(SOW, 28, date(2026, 3, 1)) == 28
    assert L.days_to_transplant(SOW, 28, date(2026, 3, 29)) == 0
    assert L.days_to_transplant(SOW, 28, date(2026, 5, 1)) == 0


def test_dates():
    assert L.germination_date(SOW, 7) == date(2026, 3, 8)
    assert L.transplant_date(SOW, 28) == date(2026, 3, 29)


@pytest.mark.parametrize("germ,trans", [(0, 10), (10, 10), (10, 5)])
def test_validation(germ, trans):
    with pytest.raises(ValueError):
        L.validate(germ, trans)
