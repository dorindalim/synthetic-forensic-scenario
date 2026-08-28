# defines the structure of incoming requests and entities etc

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

class ScenarioStatus (str, Enum):
    # diff possible states of a requested scenario
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScenarioCreateRequest(BaseModel):
    # json that is accepted by POST /api/scenarios
    model_config = ConfigDict(
        # values like "2" in the json wont be converted into int
        strict=True,
        # rejects unknown fields, dont ignore
        extra="forbid",
        # allowed config cannot change after created
        frozen=True,
    )
    
    scenario: Literal["credential_theft"]
    
    # need at least 1 user and device bcuz the events must reference existing entities
    users: int = Field(ge=1)
    devices: int = Field(ge=1)
    
    # there are 5 stages in the logical progression, total cannot be < 5
    events: int = Field(ge=5)
    
    seed: int
    
class HealthResponse(BaseModel):
    # response returned by GET /health
    status: str
    
class ErrorResponse(BaseModel):
    # used for invalid req, failure to generate a scenario or missing scenarios
    error: str
    message: str

class ForensicUser(BaseModel):
    id: str
    username: str
    role: str
    
class ForensicDevice(BaseModel):
    id: str
    hostname: str
    os: str

class ForensicEvent(BaseModel):
    id: str
    type: str
    timestamp: datetime

    # actor_user_id and device_id optional bcuz other bg events may not belong to a user/device
    actor_user_id: str | None = None
    device_id: str | None = None
    details: dict[str, Any]
    
class ScenarioMetaData(BaseModel):
    # deterministic metadata to describe the generated scenario
    
    # job creation time and job id are not included
    # they are non-deterministic operational values
    scenario: Literal["credential_theft"]
    seed: int
    requestedUsers: int
    requestedDevices: int
    requestedEvents: int

class GeneratedScenario(BaseModel):
    metadata: ScenarioMetaData
    users: list[ForensicUser]
    devices: list[ForensicDevice]
    events: list[ForensicEvent]

class ScenarioJobResponse(BaseModel):
    # response when a scenario is created or retrieved
    id: str
    status: ScenarioStatus
    created_at: datetime
    # populated after successful generation
    scenario: GeneratedScenario | None = None
    # populated after generated fail
    error: ErrorResponse | None = None