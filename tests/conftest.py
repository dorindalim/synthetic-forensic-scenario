# shared pytest features used across most test files
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.generator import generateScenario
from app.main import app
from app.schemas import (GeneratedScenario, ScenarioCreateRequest)

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    # hv a FastAPI client w/o starting Uvicorn
    with TestClient(app) as testClient:
        yield testClient

@pytest.fixture
def validRequestBody() -> dict[str, object]:
    # valid JSON body for a req
    return {
        "scenario": "credential_theft",
        "users": 2,
        "devices": 2,
        "events": 25,
        "seed": 42,
    }

@pytest.fixture
def validConfig() -> ScenarioCreateRequest:
    # valid config for a scenario generation
    return ScenarioCreateRequest(
        scenario="credential_theft",
        users=2,
        devices=2,
        events=25,
        seed=42,
    )

@pytest.fixture
def generatedScenario(validConfig: ScenarioCreateRequest) -> GeneratedScenario:
    # give 1 deterministic scenario for validation testing
    return generateScenario(validConfig)