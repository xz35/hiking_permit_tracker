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
    snapshot: dict[str, Any] | None,
    alert_events: list,
    email_result: dict[str, Any],
    previous_snapshot_loaded: bool,
    observed_at: str,
    source_status: str,
    error_message: str | None = None,
    stale_snapshot: bool = False,
) -> dict[str, Any]:
    payload = {
        "last_attempted_poll_at": observed_at,
        "last_successful_poll_at": snapshot["generated_at"] if snapshot else None,
        "source_status": source_status,
        "primary_match_count": snapshot["summary"]["primary_match_count"] if snapshot else 0,
        "alert_event_count": len(alert_events),
        "previous_snapshot_loaded": previous_snapshot_loaded,
        "stale_snapshot": stale_snapshot,
        "email": email_result,
    }
    if error_message:
        payload["error"] = error_message
    return payload


def _build_empty_snapshot(
    settings: Settings,
    observed_at: str,
    request_url: str = "",
) -> dict[str, Any]:
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
            "total_records": 0,
            "primary_match_count": 0,
        },
        "records": [],
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
    previous_snapshot = load_json_url(
        settings.previous_snapshot_url,
        timeout_seconds=settings.poll_timeout_seconds,
    )
    previous_history = load_json_url(
        settings.previous_history_url,
        timeout_seconds=settings.poll_timeout_seconds,
    )

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    latest_path = settings.output_dir / "latest.json"
    history_path = settings.output_dir / "history.json"
    status_path = settings.output_dir / "status.json"

    client = WhitneyAvailabilityClient(settings)
    fetch_error: str | None = None

    try:
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
        alert_events = find_alert_events(current_snapshot, previous_snapshot, settings)
        history_payload = _build_history(
            previous_history=previous_history,
            snapshot=current_snapshot,
            alert_events=alert_events,
            settings=settings,
        )
        source_status = "ok"
    except Exception as exc:
        fetch_error = str(exc)
        current_snapshot = previous_snapshot or _build_empty_snapshot(settings, observed_at)
        alert_events = []
        history_payload = previous_history or {
            "generated_at": observed_at,
            "events": [],
        }
        source_status = "error"

    try:
        email_result = send_email_alerts(alert_events, settings)
    except Exception as exc:
        email_result = {"sent": False, "reason": "email_error", "error": str(exc)}

    status_payload = _build_status(
        snapshot=current_snapshot,
        alert_events=alert_events,
        email_result=email_result,
        previous_snapshot_loaded=previous_snapshot is not None,
        observed_at=observed_at,
        source_status=source_status,
        error_message=fetch_error,
        stale_snapshot=fetch_error is not None and previous_snapshot is not None,
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

