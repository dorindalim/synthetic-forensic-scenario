import logging

from app.generator import generateScenario
from app.invariants import assertScenarioInvariants
from app.schemas import ScenarioCreateRequest
from app.store import (
    InMemoryScenarioStore,
    ScenarioJobRecord,
)

_logger = logging.getLogger(__name__)

class ScenarioJobManager:
    def __init__(self, store: InMemoryScenarioStore) -> None:
        self._store = store
    
    def createJob(self, config: ScenarioCreateRequest) -> ScenarioJobRecord:
        # create a new job record in the store
        return self._store.createJob(config)
    
    def runJob(self, jobId: str) -> None:
        # run the job in a separate thread
        try:
            # job start executing
            self._store.changeToRunning(jobId)
                
            # get the stored config
            job = self._store.getJob(jobId)
            if job is None:
                    raise RuntimeError(f"Job {jobId} not found in store")
                
            scenario = generateScenario(job.config)
                
            assertScenarioInvariants(scenario=scenario, config=job.config)
                
            self._store.changeToCompleted(jobId=jobId, scenario=scenario)
        except Exception as e:
            errorMessage = str(e)
            _logger.error(f"Job {jobId} failed: {errorMessage}")
            self._store.changeToFailed(jobId=jobId, errorMessage=errorMessage)