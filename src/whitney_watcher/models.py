from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class PermitRecord:
    observed_at: str
    entry_date: str
    permit_code: str
    permit_type: str
    total_capacity: int
    available_capacity: int
    is_walkup: bool
    is_primary_match: bool
    is_secondary_visible: bool
    match_reason: str | None
    source_last_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AlertEvent:
    event_type: str
    permit_type: str
    entry_date: str
    available_capacity: int
    previous_capacity: int
    observed_at: str
    is_primary_match: bool
    public_permit_url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

