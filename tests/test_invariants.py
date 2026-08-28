import pytest

from app.invariants import (
    ScenarioInvariantError,
    assertScenarioInvariants,
    validateScenarioInvariants,
)

from app.schemas import (
    GeneratedScenario,
    ScenarioCreateRequest,
)

def testValidScenarioHasNoInvariantErrors(
    generatedScenario: GeneratedScenario,
    validConfig: ScenarioCreateRequest,
) -> None:
    # valid scenario must hv no invariant errors
    errors = validateScenarioInvariants(
        scenario=generatedScenario,
        config=validConfig,
    )
    assert len(errors) == 0

def testAssertionFunctionAcceptsValidScenario(
    generatedScenario: GeneratedScenario,
    validConfig: ScenarioCreateRequest,
) -> None:
    # assert function must not raise error for valid scenario
    assertScenarioInvariants(
        scenario=generatedScenario,
        config=validConfig,
    )
    
def testDetectIncorrectUserCount(
    generatedScenario: GeneratedScenario,
    validConfig: ScenarioCreateRequest,
) -> None:
    # removing a user violates requested count
    invalidScenario = generatedScenario.model_copy(
        update={
            "users": generatedScenario.users[:-1],
        },
        deep=True,
    )
    
    violations = validateScenarioInvariants(
        scenario=invalidScenario,
        config=validConfig,
    )
    
    assert violations
    assert any(
        "users" in message.lower() for message in violations
    )
    
def testDetectDuplicateEventId(
    generatedScenario: GeneratedScenario,
    validConfig: ScenarioCreateRequest,
) -> None:
    modifiedEvents = [
        event.model_copy(deep=True) for event in generatedScenario.events
    ]
    
    modifiedEvents[1] = modifiedEvents[1].model_copy(
        update={
            "id": modifiedEvents[0].id,
        }
    )
    
    invalidScenario = generatedScenario.model_copy(
        update={
            "events": modifiedEvents,
        },
        deep=True,
    )
    
    violations = validateScenarioInvariants(
        scenario=invalidScenario,
        config=validConfig,
    )
    
    assert violations
    assert any(
        "duplicate" in message.lower() for message in violations
    )
    
def testDetectUnknownUserReference(
    generatedScenario: GeneratedScenario,
    validConfig: ScenarioCreateRequest,
) -> None:
    modifiedEvents = [
        event.model_copy(deep=True) for event in generatedScenario.events
    ]
    
    modifiedEvents[0] = modifiedEvents[0].model_copy(
        update={
            "actor_user_id": "user-does-not-exist",
        },
    )
    
    invalidScenario = generatedScenario.model_copy(
        update={
            "events": modifiedEvents,
        },
        deep=True,
    )
    
    violations = validateScenarioInvariants(
        scenario=invalidScenario,
        config=validConfig,
    )
    
    assert violations
    assert any(
        "user" in message.lower() for message in violations
    )

def testDetectUnsortedTimestamps(
    generatedScenario: GeneratedScenario,
    validConfig: ScenarioCreateRequest,
) -> None:
    # if the events are reversed, they must violate
    reversedEvents = list(reversed(generatedScenario.events))
    
    invalidScenario = generatedScenario.model_copy(
        update={
            "events": reversedEvents,
        },
        deep=True,
    )
    
    violations = validateScenarioInvariants(
        scenario=invalidScenario,
        config=validConfig,
    )
    
    assert violations
    assert any(
        "after" in message.lower() or "chronolog" in message.lower() for message in violations
    )

def testDetectMissingAttackStage(
    generatedScenario: GeneratedScenario,
    validConfig: ScenarioCreateRequest,
) -> None:
    modifiedEvents = [
        event.model_copy(deep=True) for event in generatedScenario.events
    ]
    
    for i, event in enumerate(modifiedEvents):
        if event.type == "credential_access":
            modifiedEvents[i] = event.model_copy(
                update={
                    "type": "background_activity",
                },
            )
            break
    
    invalidScenario = generatedScenario.model_copy(
        update={
            "events": modifiedEvents,
        },
        deep=True,
    )
    
    violations = validateScenarioInvariants(
        scenario=invalidScenario,
        config=validConfig,
    )
    
    assert violations
    assert any (
        "credential_access" in message or "attack chain" in message.lower() for message in violations
    )

def testRaiseAssertionErrorForInvalidScenario(
    generatedScenario: GeneratedScenario,
    validConfig: ScenarioCreateRequest,
) -> None:
    invalidScenario = generatedScenario.model_copy(
        update={
            "events": []
        },
        deep=True,
    )
    
    with pytest.raises(ScenarioInvariantError):
        assertScenarioInvariants(
            scenario=invalidScenario,
            config=validConfig,
        )