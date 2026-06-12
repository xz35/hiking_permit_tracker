from __future__ import annotations

import unittest

from whitney_watcher.alerts import booking_deep_link, find_alert_events
from whitney_watcher.config import Settings


class AlertTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings()

    def test_alert_on_transition_to_two_or_more(self) -> None:
        previous_snapshot = {
            "records": [
                {
                    "entry_date": "2026-07-03",
                    "permit_type": "overnight",
                    "available_capacity": 1,
                    "is_primary_match": False,
                }
            ]
        }
        current_snapshot = {
            "records": [
                {
                    "entry_date": "2026-07-03",
                    "permit_type": "overnight",
                    "available_capacity": 3,
                    "is_primary_match": True,
                    "observed_at": "2026-04-02T00:00:00Z",
                }
            ]
        }
        events = find_alert_events(current_snapshot, previous_snapshot, self.settings)
        self.assertEqual(1, len(events))
        self.assertEqual("primary_match_opened", events[0].event_type)

    def test_no_duplicate_alert_while_remaining_above_threshold(self) -> None:
        previous_snapshot = {
            "records": [
                {
                    "entry_date": "2026-07-03",
                    "permit_type": "overnight",
                    "available_capacity": 2,
                    "is_primary_match": True,
                }
            ]
        }
        current_snapshot = {
            "records": [
                {
                    "entry_date": "2026-07-03",
                    "permit_type": "overnight",
                    "available_capacity": 4,
                    "is_primary_match": True,
                    "observed_at": "2026-04-02T00:00:00Z",
                }
            ]
        }
        events = find_alert_events(current_snapshot, previous_snapshot, self.settings)
        self.assertEqual([], events)

    def test_day_use_alert_is_optional(self) -> None:
        self.settings.alert_day_use = True
        current_snapshot = {
            "records": [
                {
                    "entry_date": "2026-07-03",
                    "permit_type": "day_use",
                    "available_capacity": 5,
                    "is_primary_match": False,
                    "observed_at": "2026-04-02T00:00:00Z",
                }
            ]
        }
        events = find_alert_events(current_snapshot, previous_snapshot=None, settings=self.settings)
        self.assertEqual(1, len(events))
        self.assertEqual("day_use_opened", events[0].event_type)


class DeepLinkTests(unittest.TestCase):
    def test_overnight_link_includes_date_and_type(self) -> None:
        link = booking_deep_link(
            "https://www.recreation.gov/permits/445860", "2026-07-03", "overnight"
        )
        self.assertEqual(
            "https://www.recreation.gov/permits/445860/registration/"
            "detailed-availability?date=2026-07-03&type=overnight-permit",
            link,
        )

    def test_trailing_slash_in_base_is_handled(self) -> None:
        link = booking_deep_link(
            "https://www.recreation.gov/permits/445860/", "2026-07-03", "overnight"
        )
        self.assertNotIn("445860//", link)

    def test_unknown_permit_type_omits_type_param(self) -> None:
        link = booking_deep_link(
            "https://www.recreation.gov/permits/445860", "2026-07-03", "mystery"
        )
        self.assertNotIn("type=", link)
        self.assertIn("date=2026-07-03", link)


if __name__ == "__main__":
    unittest.main()
