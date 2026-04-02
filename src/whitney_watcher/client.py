from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import Settings


@dataclass(slots=True)
class FetchResult:
    payload: dict
    request_url: str
    status: str


class WhitneyAvailabilityClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch(self, start_date: date, end_date: date) -> FetchResult:
        query = urlencode(
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "commercial_acct": self.settings.commercial_acct,
            }
        )
        request_url = f"{self.settings.availability_url}?{query}"
        request = Request(
            request_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "mt-whitney-permit-watcher/1.0",
            },
        )

        try:
            with urlopen(request, timeout=self.settings.poll_timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise RuntimeError(f"Whitney API returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError(f"Whitney API request failed: {exc.reason}") from exc

        payload = json.loads(raw_body)
        if "payload" not in payload or not isinstance(payload["payload"], dict):
            raise RuntimeError("Whitney API response did not include a payload object")

        return FetchResult(payload=payload["payload"], request_url=request_url, status="ok")

