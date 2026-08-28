# stores job records as long as app is running
# has a lock cuz HTTP requests and bg generation may access dict at the same time

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from app.schemas import (
    GeneratedScenario,
    ScenarioStatus,
    ScenarioCreateRequest,
)

@dataclass(slots=True)
class ScenarioJobRecord:
    # how a scenario-generated job is represented internally
    # not returned by API bcuz it has the original config used by generator
    
    id: str
    config: ScenarioCreateRequest
    status: ScenarioStatus
    created_at: datetime
    scenario: GeneratedScenario | None = None
    error_message: str | None = None