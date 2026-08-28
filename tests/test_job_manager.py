import pytest

import app.job_manager as jobManagerModule
from app.job_manager import ScenarioJobManager
from app.schemas import (
    GeneratedScenario,
    ScenarioCreateRequest,
    ScenarioStatus,
)
from app.store import InMemoryScenarioStore


def testJobPendingToRunningToComplete(
    monkeypatch: pytest.MonkeyPatch,
    validConfig: ScenarioCreateRequest,
) -> None:

    store = InMemoryScenarioStore()
    manager = ScenarioJobManager(store)

    job = manager.createJob(validConfig)

    storedPendingJob = store.getJob(job.id)

    assert storedPendingJob is not None
    assert storedPendingJob.status == ScenarioStatus.PENDING

    observedStatuses: list[ScenarioStatus] = []

    realGenerator = jobManagerModule.generateScenario

    def observingGenerator(
        config: ScenarioCreateRequest,
    ) -> GeneratedScenario:
        # get the status once generation starts
        currentJob = store.getJob(job.id)

        assert currentJob is not None

        observedStatuses.append(currentJob.status)

        return realGenerator(config)

    monkeypatch.setattr(
        jobManagerModule,
        "generateScenario",
        observingGenerator,
    )

    manager.runJob(job.id)

    assert observedStatuses == [ScenarioStatus.RUNNING]

    completedJob = store.getJob(job.id)

    assert completedJob is not None
    assert completedJob.status == ScenarioStatus.COMPLETED
    assert completedJob.scenario is not None
    assert completedJob.errorMessage is None


def testGenerationExceptionChangesStatusToFailed(
    monkeypatch: pytest.MonkeyPatch,
    validConfig: ScenarioCreateRequest,
) -> None:

    store = InMemoryScenarioStore()
    manager = ScenarioJobManager(store)

    job = manager.createJob(validConfig)

    def failingGenerator(
        _config: ScenarioCreateRequest,
    ) -> GeneratedScenario:
        # a controlled exception will test failure
        raise RuntimeError("forced generation failure")

    monkeypatch.setattr(
        jobManagerModule,
        "generateScenario",
        failingGenerator,
    )

    manager.runJob(job.id)

    failedJob = store.getJob(job.id)

    assert failedJob is not None
    assert failedJob.status == ScenarioStatus.FAILED
    assert failedJob.scenario is None
    assert failedJob.errorMessage is not None
    assert "forced generation failure" in failedJob.errorMessage