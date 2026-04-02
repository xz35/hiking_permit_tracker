from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .calendar_logic import is_target_entry_date, iter_dates_for_months
from .config import Settings
from .models import PermitRecord


def normalize_payload(
    payload: dict[str, Any],
    settings: Settings,
    observed_at: str | None = None,
    source_last_status: str = "ok",
) -> list[PermitRecord]:
    observed_at = observed_at or datetime.now(UTC).isoformat()
    records: list[PermitRecord] = []

    for entry_day in iter_dates_for_months(settings.months):
        daily_payload = payload.get(entry_day.isoformat(), {})
        for permit_code, permit_meta in settings.permit_code_map.items():
            source_record = daily_payload.get(permit_code, {})
            permit_type = str(permit_meta["permit_type"])
            total_capacity = int(source_record.get("total", permit_meta["quota"]))
            available_capacity = int(source_record.get("remaining", 0))
            is_walkup = bool(source_record.get("is_walkup", False))
            target_day = is_target_entry_date(entry_day, settings.target_weekdays)
            is_primary_match = (
                permit_type == settings.preferred_permit_type
                and target_day
                and available_capacity >= settings.alert_threshold
            )
            is_secondary_visible = True
            match_reason = None
            if is_primary_match:
                match_reason = (
                    f"{permit_type} permit on preferred weekday with capacity "
                    f">={settings.alert_threshold}"
                )
            elif permit_type == settings.visible_secondary_permit_type and available_capacity > 0:
                match_reason = "Visible secondary permit availability"
            elif permit_type == settings.preferred_permit_type and available_capacity > 0:
                match_reason = "Overnight availability below alert threshold or off target day"

            records.append(
                PermitRecord(
                    observed_at=observed_at,
                    entry_date=entry_day.isoformat(),
                    permit_code=permit_code,
                    permit_type=permit_type,
                    total_capacity=total_capacity,
                    available_capacity=available_capacity,
                    is_walkup=is_walkup,
                    is_primary_match=is_primary_match,
                    is_secondary_visible=is_secondary_visible,
                    match_reason=match_reason,
                    source_last_status=source_last_status,
                )
            )

    return records

