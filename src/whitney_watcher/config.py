from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _parse_csv(value: str | None, default: Iterable[str]) -> list[str]:
    if value is None or value.strip() == "":
        return list(default)
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_months(values: Iterable[str]) -> list[tuple[int, int]]:
    parsed: list[tuple[int, int]] = []
    for value in values:
        year_str, month_str = value.split("-", maxsplit=1)
        parsed.append((int(year_str), int(month_str)))
    return parsed


@dataclass(slots=True)
class Settings:
    permit_id: int = 445860
    availability_url: str = (
        "https://www.recreation.gov/api/permitinyo/445860/availability"
    )
    public_permit_url: str = "https://www.recreation.gov/permits/445860"
    commercial_acct: str = "false"
    months: list[tuple[int, int]] = field(
        default_factory=lambda: [(2026, 7), (2026, 8)]
    )
    target_weekdays: set[int] = field(default_factory=lambda: {3, 4, 5})
    permit_code_map: dict[str, dict[str, int | str]] = field(
        default_factory=lambda: {
            "166": {"permit_type": "overnight", "quota": 60},
            "406": {"permit_type": "day_use", "quota": 100},
        }
    )
    preferred_permit_type: str = "overnight"
    visible_secondary_permit_type: str = "day_use"
    alert_threshold: int = 2
    poll_timeout_seconds: int = 20
    output_dir: Path = Path("build/pages")
    previous_snapshot_url: str | None = None
    previous_history_url: str | None = None
    data_public_url: str | None = None
    email_enabled: bool = False
    gmail_username: str | None = None
    gmail_app_password: str | None = None
    email_to: str | None = None
    alert_day_use: bool = False
    alert_sub_threshold_overnight: bool = False
    history_limit: int = 200

    @property
    def start_date(self) -> date:
        year, month = self.months[0]
        return date(year, month, 1)

    @property
    def end_date(self) -> date:
        year, month = self.months[-1]
        if month == 12:
            return date(year, month, 31)
        next_month = date(year + (month // 12), (month % 12) + 1, 1)
        return date.fromordinal(next_month.toordinal() - 1)

    @classmethod
    def from_env(cls, output_dir: str | None = None) -> "Settings":
        month_values = _parse_csv(
            os.getenv("WHITNEY_MONTHS"),
            default=["2026-07", "2026-08"],
        )
        weekday_values = {
            int(value)
            for value in _parse_csv(
                os.getenv("WHITNEY_TARGET_WEEKDAYS"), default=["3", "4", "5"]
            )
        }
        settings = cls(
            permit_id=_parse_int(os.getenv("WHITNEY_PERMIT_ID"), 445860),
            availability_url=os.getenv(
                "WHITNEY_AVAILABILITY_URL",
                "https://www.recreation.gov/api/permitinyo/445860/availability",
            ),
            public_permit_url=os.getenv(
                "WHITNEY_PUBLIC_PERMIT_URL",
                "https://www.recreation.gov/permits/445860",
            ),
            commercial_acct=os.getenv("WHITNEY_COMMERCIAL_ACCT", "false"),
            months=_parse_months(month_values),
            target_weekdays=weekday_values,
            preferred_permit_type=os.getenv(
                "WHITNEY_PREFERRED_PERMIT_TYPE", "overnight"
            ),
            visible_secondary_permit_type=os.getenv(
                "WHITNEY_VISIBLE_SECONDARY_PERMIT_TYPE", "day_use"
            ),
            alert_threshold=_parse_int(os.getenv("WHITNEY_ALERT_THRESHOLD"), 2),
            poll_timeout_seconds=_parse_int(
                os.getenv("WHITNEY_TIMEOUT_SECONDS"), 20
            ),
            output_dir=Path(output_dir or os.getenv("WHITNEY_OUTPUT_DIR", "build/pages")),
            previous_snapshot_url=os.getenv("WHITNEY_PREVIOUS_SNAPSHOT_URL"),
            previous_history_url=os.getenv("WHITNEY_PREVIOUS_HISTORY_URL"),
            data_public_url=os.getenv("WHITNEY_DATA_PUBLIC_URL"),
            email_enabled=_parse_bool(os.getenv("WHITNEY_EMAIL_ENABLED"), False),
            gmail_username=os.getenv("WHITNEY_GMAIL_USERNAME"),
            gmail_app_password=os.getenv("WHITNEY_GMAIL_APP_PASSWORD"),
            email_to=os.getenv("WHITNEY_EMAIL_TO"),
            alert_day_use=_parse_bool(os.getenv("WHITNEY_ALERT_DAY_USE"), False),
            alert_sub_threshold_overnight=_parse_bool(
                os.getenv("WHITNEY_ALERT_SUB_THRESHOLD_OVERNIGHT"), False
            ),
            history_limit=_parse_int(os.getenv("WHITNEY_HISTORY_LIMIT"), 200),
        )
        settings.months.sort()
        return settings

