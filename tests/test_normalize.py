from __future__ import annotations

import unittest

from whitney_watcher.config import Settings
from whitney_watcher.normalize import normalize_payload


class NormalizePayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings()

    def test_primary_match_requires_overnight_on_target_day_with_capacity_two_or_more(self) -> None:
        payload = {
            "2026-07-02": {"166": {"total": 60, "remaining": 3, "is_walkup": False}},
            "2026-07-06": {"166": {"total": 60, "remaining": 3, "is_walkup": False}},
        }
        records = normalize_payload(payload, self.settings, observed_at="2026-04-02T00:00:00Z")
        july_2 = next(
            record
            for record in records
            if record.entry_date == "2026-07-02" and record.permit_type == "overnight"
        )
        july_6 = next(
            record
            for record in records
            if record.entry_date == "2026-07-06" and record.permit_type == "overnight"
        )
        self.assertTrue(july_2.is_primary_match)
        self.assertFalse(july_6.is_primary_match)

    def test_dates_missing_from_api_are_normalized_as_zero_capacity(self) -> None:
        records = normalize_payload({}, self.settings, observed_at="2026-04-02T00:00:00Z")
        july_1_day_use = next(
            record
            for record in records
            if record.entry_date == "2026-07-01" and record.permit_type == "day_use"
        )
        self.assertEqual(0, july_1_day_use.available_capacity)
        self.assertTrue(july_1_day_use.is_secondary_visible)

    def test_day_use_stays_visible_but_is_not_primary_match(self) -> None:
        payload = {
            "2026-07-03": {"406": {"total": 100, "remaining": 9, "is_walkup": False}}
        }
        records = normalize_payload(payload, self.settings, observed_at="2026-04-02T00:00:00Z")
        day_use = next(
            record
            for record in records
            if record.entry_date == "2026-07-03" and record.permit_type == "day_use"
        )
        self.assertTrue(day_use.is_secondary_visible)
        self.assertFalse(day_use.is_primary_match)


if __name__ == "__main__":
    unittest.main()

