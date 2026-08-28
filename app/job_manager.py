import logging

from app.generator import generateScenario
from app.invariants import assertScenarioInvariants
from app.schemas import ScenarioCreateRequest
from app.store import (
    InMemoryScenarioStore,
    ScenarioJobRecord,
)

logger = logging.getLogger(__name__)

class ScenarioJobManager:
    def __init__(self, store: InMemoryScenarioStore) -> None:
        self.store = store
    
    def createJob(self, config: ScenarioCreateRequest) -> ScenarioJobRecord:
        # create a new job record in the store
        return self.store.createJob(config)
    
    def runJob(self, jobId: str) -> None:
        # run the job in a separate thread
        try:
            # job start executing
            self.store.changeToRunning(jobId)
                
            # get the stored config
            job = self.store.getJob(jobId)
            if job is None:
                    raise RuntimeError(f"Job {jobId} not found in store")
                
            scenario = generate_scenario(job.config)
                
            assertScenarioInvariants(scenario=scenario, config=job.config)
                
            self.store.changeToCompleted(jobId=jobId, scenario=scenario)
        except Exception as e:
            errorMessage = str(e)
            logger.error(f"Job {jobId} failed: {errorMessage}")
            self.store.changeToFailed(jobId=jobId, error_message=errorMessage)