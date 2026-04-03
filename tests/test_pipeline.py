from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from whitney_watcher.client import FetchResult
from whitney_watcher.config import Settings
from whitney_watcher.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_fetch_failure_reuses_previous_snapshot_and_writes_error_status(self) -> None:
        previous_snapshot = {
            "generated_at": "2026-04-01T00:00:00Z",
            "summary": {"primary_match_count": 1},
            "records": [],
        }
        previous_history = {
            "generated_at": "2026-04-01T00:00:00Z",
            "events": [{"generated_at": "2026-04-01T00:00:00Z"}],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(
                output_dir=Path(temp_dir),
                previous_snapshot_url="https://example.com/latest.json",
                previous_history_url="https://example.com/history.json",
            )
            with patch(
                "whitney_watcher.pipeline.load_json_url",
                side_effect=[previous_snapshot, previous_history],
            ), patch(
                "whitney_watcher.pipeline.WhitneyAvailabilityClient.fetch",
                side_effect=RuntimeError("api down"),
            ):
                run_pipeline(settings)

            latest_payload = json.loads((Path(temp_dir) / "latest.json").read_text(encoding="utf-8"))
            history_payload = json.loads((Path(temp_dir) / "history.json").read_text(encoding="utf-8"))
            status_payload = json.loads((Path(temp_dir) / "status.json").read_text(encoding="utf-8"))

        self.assertEqual(previous_snapshot, latest_payload)
        self.assertEqual(previous_history, history_payload)
        self.assertEqual("error", status_payload["source_status"])
        self.assertTrue(status_payload["stale_snapshot"])
        self.assertIn("api down", status_payload["error"])

    def test_email_failure_does_not_block_snapshot_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(output_dir=Path(temp_dir))
            fetch_result = FetchResult(
                payload={},
                request_url="https://example.com/availability",
                status="ok",
            )
            with patch(
                "whitney_watcher.pipeline.load_json_url",
                side_effect=[None, None],
            ), patch(
                "whitney_watcher.pipeline.WhitneyAvailabilityClient.fetch",
                return_value=fetch_result,
            ), patch(
                "whitney_watcher.pipeline.send_email_alerts",
                side_effect=RuntimeError("smtp failure"),
            ):
                run_pipeline(settings)

            latest_payload = json.loads((Path(temp_dir) / "latest.json").read_text(encoding="utf-8"))
            status_payload = json.loads((Path(temp_dir) / "status.json").read_text(encoding="utf-8"))

        self.assertEqual("ok", status_payload["source_status"])
        self.assertEqual("email_error", status_payload["email"]["reason"])
        self.assertIn("smtp failure", status_payload["email"]["error"])
        self.assertIn("summary", latest_payload)


if __name__ == "__main__":
    unittest.main()
