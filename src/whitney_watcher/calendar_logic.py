from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Iterator


def iter_dates_for_months(months: list[tuple[int, int]]) -> Iterator[date]:
    for year, month in months:
        _, days_in_month = monthrange(year, month)
        for day in range(1, days_in_month + 1):
            yield date(year, month, day)


def is_target_entry_date(entry_date: date, target_weekdays: set[int]) -> bool:
    return entry_date.weekday() in target_weekdays
