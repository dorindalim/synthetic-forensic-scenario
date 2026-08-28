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

def _generateRequiredEvents(
    rng: random.Random,
    baseTimestamp: datetime,
    victimUser: ForensicUser,
    victimDevice: ForensicDevice,
) -> list[_EventDraft]:
    # generate the 5 required events for a credential theft scenario
    
    eventDraft: list[_EventDraft] = []
    
    # every required event occurs 1-5 mins after prev event
    timestamps: list[datetime] = []
    currentTime = baseTimestamp
    for _ in range(5):
        currentTime += timedelta(minutes=rng.randint(1, 5))
        timestamps.append(currentTime)
    return [
        _EventDraft(
            event_type="authentication",
            timestamp=timestamps[0],
            actor_user_id=victimUser.id,
            device_id=victimDevice.id,
            details={
                "result": "success",
                "method": "password",
                "source_ip": f"198.51.100.{rng.randint(1, 254)}",
            },
            insertion_order=0
        ),
        _EventDraft(
            event_type="process_execution",
            timestamp=timestamps[1],
            actor_user_id=victimUser.id,
            device_id=victimDevice.id,
            details={
                "process_name": rng.choice(("powershell.exe", "cmd.exe", "explorer.exe")),
                "parent_process": "explorer.exe",
                "process_id": rng.randint(1000, 9999),
            },
            insertion_order=1
        ),
        _EventDraft(
            event_type="credential_access",
            timestamp=timestamps[2],
            actor_user_id=victimUser.id,
            device_id=victimDevice.id,
            details={
                "method": rng.choice(("browser_credential_store", "cached_credentials", "memory_credentials")),
                "target": "local_user_credentials",
            },
            insertion_order=2
        ),
        _EventDraft(
            event_type="network_connection",
            timestamp=timestamps[3],
            actor_user_id=victimUser.id,
            device_id=victimDevice.id,
            details={
                "destination_ip": f"203.0.113.{rng.randint(1, 254)}",
                "destination_port": 443,
                "protocol": "tcp",
            },
            insertion_order=3
        ),
        _EventDraft(
            event_type="data_exfiltration",
            timestamp=timestamps[4],
            actor_user_id=victimUser.id,
            device_id=victimDevice.id,
            details={
                "channel": "https",
                "data_type": "credential_archive",
                "bytes_transferred": rng.randint(50_000, 5_000_000),
            },
            insertion_order=4
        ),
    ]
    
def _generateBackgroundEvent(
    rng: random.Random,
    users: list[ForensicUser],
    devices: list[ForensicDevice],
    baseTimestamp: datetime,
    latestTimestamp: datetime,
    insertion_order: int
) -> _EventDraft:
    # generate a single background event that is not part of the credential theft attack
    eventType = rng.choice(
        (
            "file_access",
            "dns_query",
            "system_service",
            "user_activity",
        )
    )
    actor = rng.choice(users)
    device = rng.choice(devices)
    
    # bg activity can happen beore during or after attack
    availableSeconds = int((latestTimestamp - baseTimestamp + timedelta(minutes=10)).total_seconds())
    
    timestamp = baseTimestamp + timedelta(seconds=rng.randint(0, availableSeconds))
    
    if eventType == "file_access":
        details: dict[str, Any] = {
            "path": (
                f"C:\\Users\\{actor.username}\\Documents\\"
                f"report-{rng.randint(1, 20)}.docx"
            ),
            "operation": rng.choice(("open", "read", "close")),
        }

    elif eventType == "dns_query":
        details = {
            "query": rng.choice(
                (
                    "updates.example",
                    "intranet.example",
                    "files.example",
                )
            ),
            "resolved_ip": f"192.0.2.{rng.randint(1, 254)}",
        }

    elif eventType == "system_service":
        details = {
            "service": rng.choice(
                (
                    "update_service",
                    "backup_service",
                    "endpoint_monitor",
                )
            ),
            "state": rng.choice(("started", "stopped", "running")),
        }

    else:
        details = {
            "action": rng.choice(
                (
                    "screen_unlock",
                    "application_open",
                    "session_idle",
                )
            )
        }

    return _EventDraft(
        event_type=eventType,
        timestamp=timestamp,
        actor_user_id=actor.id,
        device_id=device.id,
        details=details,
        insertion_order=insertion_order,
    )
    
def generateScenario(
    config: ScenarioCreateRequest,
) -> GeneratedScenario:
    # generated 1 complete deterministic credential-theft scenario
    # same config and seed produce same users, devices and events
    
    rng = random.Random(config.seed)
    
    users = _generateUsers(config.users, rng)
    devices = _generateDevices(config.devices, rng)
    
    # base time is produced from seed rng, rather than current time, to make the scenario deterministic
    baseTimestamp = datetime(
        year = 2025, month = 1, day = 1, tzinfo = timezone.utc
    ) + timedelta(
        days=rng.randrange(365), hours=rng.randrange(24), minutes=rng.randrange(60),
    )
    
    # one user and device as victime of the credential theft, the rest are bg users and devices
    victimUser = rng.choice(users)
    victimDevice = rng.choice(devices)
    
    # create the 5 needed events
    eventDraft = _generateRequiredEvents(
        rng=rng,
        baseTimestamp=baseTimestamp,
        victimUser=victimUser,
        victimDevice=victimDevice
    )
    
    attackEndTime = eventDraft[-1].timestamp
    backgroundEventCount = config.events - len(eventDraft)
    
    for i in range(backgroundEventCount):
        eventDraft.append(
            _generateBackgroundEvent(
                rng=rng,
                baseTimestamp=baseTimestamp,
                latestTimestamp=attackEndTime,
                users=users,
                devices=devices,
                insertion_order=len(eventDraft)
            )
        )
    
    # sort all events by timestamp and insertion order, then assign unique event ids
    eventDraft.sort(key=lambda e: (e.timestamp, e.insertion_order))
    events = [
        ForensicEvent(
            id=f"event-{i:03d}",
            type=e.event_type,
            timestamp=e.timestamp,
            actor_user_id=e.actor_user_id,
            device_id=e.device_id,
            details=e.details
        )
        for i, e in enumerate(eventDraft, start=1)
    ]
    
    metadata = ScenarioMetaData(
        scenario=config.scenario,
        seed=config.seed,
        requestedUsers=config.users,
        requestedDevices=config.devices,
        requestedEvents=config.events
    )
    
    return GeneratedScenario(
        metadata=metadata,
        users=users,
        devices=devices,
        events=events
    )