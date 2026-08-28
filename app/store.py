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
    createdAt: datetime
    scenario: GeneratedScenario | None = None
    errorMessage: str | None = None
    
class InMemoryScenarioStore:
    # data lost when app stops
    # manages all job records, like mini db
    def __init__(self) -> None:
        # creates a dict where the key is the job id and value is job record
        self._jobs: dict[str, ScenarioJobRecord] = {}
        # locks the dict when accessed by multiple threads
        self._lock = RLock()
    
    def createJob(
        self, config: ScenarioCreateRequest,
    ) -> ScenarioJobRecord:
        # creates a new job when POST is received where input is the validated req
        
        # get the lock
        with self._lock:
            # creates a unique job id and checks for collision
            while True:
                jobId = f"scenario-{uuid4().hex[:12]}"
                if jobId not in self._jobs:
                    break
            
            # create the record and store into the dict
            record = ScenarioJobRecord(
                id=jobId,
                config=config,
                status=ScenarioStatus.PENDING,
                createdAt=datetime.now(timezone.utc)
            )
            self._jobs[jobId] = record
            
            return deepcopy(record)
    
    def getJob(self, jobId: str) -> ScenarioJobRecord | None:
        # get a job by the id
        with self._lock:
            record = self._jobs.get(jobId)
            # no record exist
            if record is None:
                return None
            return deepcopy(record)
        
    def changeToRunning(self, jobId: str) -> None:
        with self._lock:
            record = self._getExistingJob(jobId)
            # anything but a pending is not allowed
            if record.status != ScenarioStatus.PENDING:
                raise RuntimeError(
                    f"Job {jobId} cannot move from "
                    f"{record.status.value} to running"
                )
            record.status = ScenarioStatus.RUNNING
            record.errorMessage = None
    
    def changeToCompleted(self, jobId: str, scenario: GeneratedScenario) -> None:
        with self._lock:
            record = self._getExistingJob(jobId)
            # anything but a running is not allowed
            if record.status != ScenarioStatus.RUNNING:
                raise RuntimeError(
                    f"Job {jobId} cannot move from "
                    f"{record.status.value} to completed"
                )
            record.scenario = scenario
            record.status = ScenarioStatus.COMPLETED
            record.errorMessage = None
    
    def changeToFailed(self, jobId: str, errorMessage: str) -> None:
        with self._lock:
            record = self._getExistingJob(jobId)
            if record.status not in {
                ScenarioStatus.PENDING, ScenarioStatus.RUNNING,
            }:
                raise RuntimeError(
                    f"Job {jobId} cannot move from "
                    f"{record.status.value} to failed"
                )
            record.status = ScenarioStatus.FAILED
            record.scenario = None
            record.errorMessage = errorMessage
    
    def _getExistingJob(self, jobId: str) -> ScenarioJobRecord:
        record = self._jobs.get(jobId)
        if record is None:
            raise KeyError(f"Scenario job {jobId} does not exist")
        return record