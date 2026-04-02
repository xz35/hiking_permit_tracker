from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from .config import Settings
from .models import AlertEvent


def _record_key(record: dict[str, Any]) -> tuple[str, str]:
    return str(record["entry_date"]), str(record["permit_type"])


def find_alert_events(
    current_snapshot: dict[str, Any],
    previous_snapshot: dict[str, Any] | None,
    settings: Settings,
) -> list[AlertEvent]:
    previous_records = {
        _record_key(record): record
        for record in (previous_snapshot or {}).get("records", [])
    }
    events: list[AlertEvent] = []

    for record in current_snapshot["records"]:
        current_key = _record_key(record)
        previous = previous_records.get(current_key, {})
        current_capacity = int(record["available_capacity"])
        previous_capacity = int(previous.get("available_capacity", 0))
        is_primary_match = bool(record["is_primary_match"])
        permit_type = str(record["permit_type"])
        opened_above_threshold = (
            permit_type == settings.preferred_permit_type
            and current_capacity >= settings.alert_threshold
            and previous_capacity < settings.alert_threshold
            and is_primary_match
        )
        if opened_above_threshold:
            events.append(
                AlertEvent(
                    event_type="primary_match_opened",
                    permit_type=permit_type,
                    entry_date=str(record["entry_date"]),
                    available_capacity=current_capacity,
                    previous_capacity=previous_capacity,
                    observed_at=str(record["observed_at"]),
                    is_primary_match=is_primary_match,
                    public_permit_url=settings.public_permit_url,
                )
            )
            continue

        day_use_opened = (
            settings.alert_day_use
            and permit_type == settings.visible_secondary_permit_type
            and current_capacity > 0
            and previous_capacity == 0
        )
        if day_use_opened:
            events.append(
                AlertEvent(
                    event_type="day_use_opened",
                    permit_type=permit_type,
                    entry_date=str(record["entry_date"]),
                    available_capacity=current_capacity,
                    previous_capacity=previous_capacity,
                    observed_at=str(record["observed_at"]),
                    is_primary_match=False,
                    public_permit_url=settings.public_permit_url,
                )
            )
            continue

        sub_threshold_overnight_opened = (
            settings.alert_sub_threshold_overnight
            and permit_type == settings.preferred_permit_type
            and 0 < current_capacity < settings.alert_threshold
            and previous_capacity == 0
        )
        if sub_threshold_overnight_opened:
            events.append(
                AlertEvent(
                    event_type="overnight_below_threshold_opened",
                    permit_type=permit_type,
                    entry_date=str(record["entry_date"]),
                    available_capacity=current_capacity,
                    previous_capacity=previous_capacity,
                    observed_at=str(record["observed_at"]),
                    is_primary_match=False,
                    public_permit_url=settings.public_permit_url,
                )
            )

    return events


def send_email_alerts(events: list[AlertEvent], settings: Settings) -> dict[str, Any]:
    if not events:
        return {"sent": False, "reason": "no_events"}
    if not settings.email_enabled:
        return {"sent": False, "reason": "email_disabled"}
    if not settings.gmail_username or not settings.gmail_app_password or not settings.email_to:
        return {"sent": False, "reason": "missing_email_configuration"}

    message = EmailMessage()
    message["Subject"] = f"Mt. Whitney permit alert: {len(events)} new opening(s)"
    message["From"] = settings.gmail_username
    message["To"] = settings.email_to

    lines = [
        "Mt. Whitney permit watcher found new availability.",
        "",
    ]
    for event in events:
        lines.extend(
            [
                f"- {event.entry_date}: {event.permit_type} now has {event.available_capacity} available "
                f"(previously {event.previous_capacity})",
                f"  Event: {event.event_type}",
                f"  Primary match: {'yes' if event.is_primary_match else 'no'}",
                f"  Observed at: {event.observed_at}",
                f"  Recreation.gov: {event.public_permit_url}",
                "",
            ]
        )

    message.set_content("\n".join(lines))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.gmail_username, settings.gmail_app_password)
        server.send_message(message)

    return {"sent": True, "count": len(events)}

