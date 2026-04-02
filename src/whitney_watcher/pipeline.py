from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .alerts import find_alert_events, send_email_alerts
from .client import WhitneyAvailabilityClient
from .config import Settings
from .normalize import normalize_payload
from .storage import load_json_url, write_json


def _build_snapshot(
    records: list,
    settings: Settings,
    observed_at: str,
    request_url: str,
) -> dict[str, Any]:
    primary_match_count = sum(1 for record in records if record.is_primary_match)
    return {
        "generated_at": observed_at,
        "permit_id": settings.permit_id,
        "public_permit_url": settings.public_permit_url,
        "source": {
            "availability_url": request_url,
            "months": [f"{year:04d}-{month:02d}" for year, month in settings.months],
            "preferred_permit_type": settings.preferred_permit_type,
            "visible_secondary_permit_type": settings.visible_secondary_permit_type,
            "alert_threshold": settings.alert_threshold,
        },
        "summary": {
            "total_records": len(records),
            "primary_match_count": primary_match_count,
        },
        "records": [record.to_dict() for record in records],
    }


def _build_status(
    snapshot: dict[str, Any],
    alert_events: list,
    email_result: dict[str, Any],
    previous_snapshot_loaded: bool,
) -> dict[str, Any]:
    return {
        "last_successful_poll_at": snapshot["generated_at"],
        "source_status": "ok",
        "primary_match_count": snapshot["summary"]["primary_match_count"],
        "alert_event_count": len(alert_events),
        "previous_snapshot_loaded": previous_snapshot_loaded,
        "email": email_result,
    }


def _build_history(
    previous_history: dict[str, Any] | None,
    snapshot: dict[str, Any],
    alert_events: list,
    settings: Settings,
) -> dict[str, Any]:
    previous_events = list((previous_history or {}).get("events", []))
    previous_events.append(
        {
            "generated_at": snapshot["generated_at"],
            "primary_match_count": snapshot["summary"]["primary_match_count"],
            "alert_events": [event.to_dict() for event in alert_events],
        }
    )
    return {
        "generated_at": snapshot["generated_at"],
        "events": previous_events[-settings.history_limit :],
    }


def run_pipeline(settings: Settings) -> dict[str, Any]:
    observed_at = datetime.now(UTC).isoformat()
    client = WhitneyAvailabilityClient(settings)
    fetch_result = client.fetch(settings.start_date, settings.end_date)
    records = normalize_payload(
        payload=fetch_result.payload,
        settings=settings,
        observed_at=observed_at,
        source_last_status=fetch_result.status,
    )
    current_snapshot = _build_snapshot(
        records=records,
        settings=settings,
        observed_at=observed_at,
        request_url=fetch_result.request_url,
    )
    previous_snapshot = load_json_url(
        settings.previous_snapshot_url,
        timeout_seconds=settings.poll_timeout_seconds,
    )
    previous_history = load_json_url(
        settings.previous_history_url,
        timeout_seconds=settings.poll_timeout_seconds,
    )
    alert_events = find_alert_events(current_snapshot, previous_snapshot, settings)
    email_result = send_email_alerts(alert_events, settings)

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    latest_path = settings.output_dir / "latest.json"
    history_path = settings.output_dir / "history.json"
    status_path = settings.output_dir / "status.json"

    history_payload = _build_history(
        previous_history=previous_history,
        snapshot=current_snapshot,
        alert_events=alert_events,
        settings=settings,
    )
    status_payload = _build_status(
        snapshot=current_snapshot,
        alert_events=alert_events,
        email_result=email_result,
        previous_snapshot_loaded=previous_snapshot is not None,
    )

    write_json(latest_path, current_snapshot)
    write_json(history_path, history_payload)
    write_json(status_path, status_payload)

    return {
        "latest_path": str(latest_path),
        "history_path": str(history_path),
        "status_path": str(status_path),
        "alert_events": [event.to_dict() for event in alert_events],
        "email_result": email_result,
    }

