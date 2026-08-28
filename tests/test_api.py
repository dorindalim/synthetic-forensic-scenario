import time
from typing import Any

import pytest
from fastapi.testclient import TestClient


def _createAndRetrieveCompletedScenario(
    client: TestClient,
    requestBody: dict[str, object],
) -> dict[str, Any]:
    createResponse = client.post(
        "/api/scenarios",
        json=requestBody,
    )

    assert createResponse.status_code == 202

    jobId = createResponse.json()["id"]

    for _ in range(100):
        getResponse = client.get(
            f"/api/scenarios/{jobId}"
        )

        assert getResponse.status_code == 200

        responseBody = getResponse.json()
        currentStatus = responseBody["status"]

        if currentStatus == "completed":
            return responseBody

        if currentStatus == "failed":
            pytest.fail(
                "Scenario generation unexpectedly failed: "
                f"{responseBody}"
            )

        time.sleep(0.01)

    pytest.fail(
        f"Scenario {jobId} did not complete "
        "within the expected time"
    )


def testHealthEndpointReturnsOk(
    client: TestClient,
) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def testCreateScenarioReturns202AndLocation(
    client: TestClient,
    validRequestBody: dict[str, object],
) -> None:
    response = client.post(
        "/api/scenarios",
        json=validRequestBody,
    )

    assert response.status_code == 202

    responseBody = response.json()

    assert responseBody["id"].startswith("scenario-")
    assert responseBody["status"] == "pending"
    assert "createdAt" in responseBody

    expectedLocation = (
        f"/api/scenarios/{responseBody['id']}"
    )

    assert response.headers["Location"] == expectedLocation

    assert "scenario" not in responseBody
    assert "error" not in responseBody


def testCompletedScenarioCanBeRetrieved(
    client: TestClient,
    validRequestBody: dict[str, object],
) -> None:
    responseBody = _createAndRetrieveCompletedScenario(
        client=client,
        requestBody=validRequestBody,
    )

    assert responseBody["status"] == "completed"
    assert "scenario" in responseBody
    assert "error" not in responseBody

    scenario = responseBody["scenario"]

    assert len(scenario["users"]) == 2
    assert len(scenario["devices"]) == 2
    assert len(scenario["events"]) == 25


@pytest.mark.parametrize(
    ("fieldName", "invalidValue"),
    [
        ("scenario", "malware_attack"),
        ("users", 0),
        ("devices", 0),
        ("events", 4),
        ("seed", "42"),
    ],
)
def testInvalidConfigurationReturns400(
    client: TestClient,
    validRequestBody: dict[str, object],
    fieldName: str,
    invalidValue: object,
) -> None:
    invalidBody = validRequestBody.copy()
    invalidBody[fieldName] = invalidValue

    response = client.post(
        "/api/scenarios",
        json=invalidBody,
    )

    assert response.status_code == 400

    responseBody = response.json()

    assert responseBody["error"] == "invalid_configuration"
    assert isinstance(responseBody["message"], str)
    assert responseBody["message"]


@pytest.mark.parametrize(
    "missingField",
    [
        "scenario",
        "users",
        "devices",
        "events",
        "seed",
    ],
)
def testMissingRequiredFieldReturns400(
    client: TestClient,
    validRequestBody: dict[str, object],
    missingField: str,
) -> None:
    invalidBody = validRequestBody.copy()
    invalidBody.pop(missingField)

    response = client.post(
        "/api/scenarios",
        json=invalidBody,
    )

    assert response.status_code == 400

    responseBody = response.json()

    assert responseBody["error"] == "invalid_configuration"
    assert missingField in responseBody["message"]


def testExtraConfigurationFieldReturns400(
    client: TestClient,
    validRequestBody: dict[str, object],
) -> None:
    invalidBody = validRequestBody.copy()
    invalidBody["unknownField"] = "unexpected value"

    response = client.post(
        "/api/scenarios",
        json=invalidBody,
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_configuration"


def testMalformedJsonReturns400(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/scenarios",
        content='{"scenario": "credential_theft",',
        headers={
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 400

    responseBody = response.json()

    assert responseBody["error"] == "invalid_configuration"
    assert "malformed JSON" in responseBody["message"]


def testUnknownScenarioIdReturns404(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/scenarios/does-not-exist"
    )

    assert response.status_code == 404

    responseBody = response.json()

    assert responseBody["error"] == "scenario_not_found"
    assert "does-not-exist" in responseBody["message"]