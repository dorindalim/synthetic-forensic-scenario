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
    
def _generateUsers(count: int, rng: random.Random) -> list[ForensicUser]:
    # generate unique users with deterministic usernames and roles
    
    users: list[ForensicUser] = []
    for i in range(count):
        baseName = USERNAME[i % len(USERNAME)]
        # add a suffix after all the base names are used, to make the usernames unique
        # e.g. 9th user will be alice2
        cycleCount = i // len(USERNAME)
        suffix = "" if cycleCount == 0 else str(cycleCount + 1)
        
        users.append(
            ForensicUser(
                id=f"user-{i:03d}",
                username=f"{baseName}{suffix}",
                role=rng.choice(USER_ROLES)
            )
        )
    return users

def _generateDevices(count: int, rng: random.Random) -> list[ForensicDevice]:
    # generate unique devices with deterministic hostnames and os
    
    devices: list[ForensicDevice] = []
    for i in range(count):
        devices.append(
            ForensicDevice(
                id=f"device-{i:03d}",
                hostname=(f"{rng.choice(DEVICES)}-{i + 1:03d}"),
                os=rng.choice(OS)
            )
        )
    return devices