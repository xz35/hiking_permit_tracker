from __future__ import annotations

import unittest
from datetime import date

from whitney_watcher.calendar_logic import is_target_entry_date, iter_dates_for_months


class CalendarLogicTests(unittest.TestCase):
    def test_iter_dates_for_months_yields_all_days(self) -> None:
        dates = list(iter_dates_for_months([(2026, 7)]))
        self.assertEqual(date(2026, 7, 1), dates[0])
        self.assertEqual(date(2026, 7, 31), dates[-1])
        self.assertEqual(31, len(dates))

    def test_target_weekdays_match_thursday_friday_saturday(self) -> None:
        target_weekdays = {3, 4, 5}
        self.assertTrue(is_target_entry_date(date(2026, 7, 2), target_weekdays))
        self.assertTrue(is_target_entry_date(date(2026, 7, 3), target_weekdays))
        self.assertTrue(is_target_entry_date(date(2026, 7, 4), target_weekdays))
        self.assertFalse(is_target_entry_date(date(2026, 7, 5), target_weekdays))


if __name__ == "__main__":
    unittest.main()

