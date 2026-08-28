import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas import (
    ForensicDevice,
    ForensicEvent,
    ForensicUser,
    GeneratedScenario,
    ScenarioCreateRequest,
    ScenarioMetaData,
)

USERNAME = (
    "Alice",
    "Benjamin",
    "Charlie",
    "Darlie",
    "Ethan",
    "Farrice",
    "Grace",
    "Henry",
)

USER_ROLES = (
    "Employee",
    "Administrator",
)

DEVICES = (
    "WORKSTATION",
    "LAPTOP",
    "DESKTOP",
)

OS = (
    "Windows 10",
    "macOS",
    "Windows 11",
)

@dataclass(slots=True)
class _EventDraft:
    # event representation before final event ids are given
    
    event_type: str
    timestamp: datetime
    actor_user_id: str | None
    device_id: str | None
    details: dict[str, Any]
    
    # deterministic 2nd sorting value when 2 events hv same timestamp
    insertion_order: int