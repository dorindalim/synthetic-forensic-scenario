from datetime import datetime

from app.generator import generateScenario
from app.invariants import REQUIRED_ATTACK_CHAIN
from app.schemas import (
    GeneratedScenario,
    ScenarioCreateRequest,
)

def testSameConfigurationAndSeedAreDeterministic(
    validConfig: ScenarioCreateRequest,
) -> None:
    # same seed and config must hv same output
    scenario1 = generateScenario(validConfig)
    scenario2 = generateScenario(validConfig)
    
    output1 = scenario1.model_dump(
        mode="json",
        by_alias=True,
    )
    output2 = scenario2.model_dump(
        mode="json",
        by_alias=True,
    )
    assert output1 == output2

def testDifferentSeedsDifferentOutput() -> None:
    # 2 diff seed hv diff output
    config1 = ScenarioCreateRequest(
        scenario="credential_theft",
        users=2,
        devices=2,
        events=25,
        seed=42,
    )
    config2 = ScenarioCreateRequest(
        scenario="credential_theft",
        users=2,
        devices=2,
        events=25,
        seed=123,
    )
    scenario1 = generateScenario(config1)
    scenario2 = generateScenario(config2)
    output1 = scenario1.model_dump(
        mode="json",
        by_alias=True,
    )
    output2 = scenario2.model_dump(
        mode="json",
        by_alias=True,
    )
    assert output1 != output2

def testRequestedCountsMatchOutput(
    generatedScenario: GeneratedScenario,
    validConfig: ScenarioCreateRequest,
) -> None:
    # generated scenario must hv same counts as requested in config
    assert len(generatedScenario.users) == validConfig.users
    assert len(generatedScenario.devices) == validConfig.devices
    assert len(generatedScenario.events) == validConfig.events
    
def testMetadataMatchConfig(
    generatedScenario: GeneratedScenario,
    validConfig: ScenarioCreateRequest,
) -> None:
    # generated scenario metadata must match the config used to generate it
    metadata = generatedScenario.metadata
    
    assert metadata.scenario == validConfig.scenario
    assert metadata.seed == validConfig.seed
    
    assert metadata.requestedUsers == validConfig.users
    assert metadata.requestedDevices == validConfig.devices
    assert metadata.requestedEvents == validConfig.events
    
def testUniqueGeneratedIds(generatedScenario: GeneratedScenario) -> None:
    # ids must be unique across all generated entities
    allIds = set()
    for user in generatedScenario.users:
        assert user.id not in allIds
        allIds.add(user.id)
    for device in generatedScenario.devices:
        assert device.id not in allIds
        allIds.add(device.id)
    for event in generatedScenario.events:
        assert event.id not in allIds
        allIds.add(event.id)
    
def testValidEventReferences(generatedScenario: GeneratedScenario) -> None:
    # all events must reference existing users and devices
    userIds = {user.id for user in generatedScenario.users}
    deviceIds = {device.id for device in generatedScenario.devices}
    
    for event in generatedScenario.events:
        if event.actor_user_id is not None:
            assert event.actor_user_id in userIds
        if event.device_id is not None:
            assert event.device_id in deviceIds
    
def testValidContextAndTimestamps(generatedScenario: GeneratedScenario) -> None:
    for event in generatedScenario.events:
        assert event.id
        assert event.type
        # check timestamp is datetime object, not another type
        assert isinstance(event.timestamp, datetime)
        # check timestamp has timezone info
        assert event.timestamp.tzinfo is not None
        # check timestamp has utc offset
        assert event.timestamp.utcoffset() is not None
        assert event.details

def testEventsAreChronological(generatedScenario: GeneratedScenario) -> None:
    # events in increasing timestamps
    timestamps = [event.timestamp for event in generatedScenario.events]
    assert timestamps == sorted(timestamps)

def testPresentAttackEventTypes(generatedScenario: GeneratedScenario) -> None:
    generatedTypes = {event.type for event in generatedScenario.events}
    for neededType in REQUIRED_ATTACK_CHAIN:
        assert neededType in generatedTypes
        
def testAttackChainOrder(generatedScenario: GeneratedScenario) -> None:
    attackEvents = [
        next(
            event for event in generatedScenario.events
            if event.type == neededType
        )
        for neededType in REQUIRED_ATTACK_CHAIN
    ]
    attackTimestamps = [event.timestamp for event in attackEvents]
    assert all(
        attackTimestamps[i] < attackTimestamps[i + 1]
        for i in range(len(attackTimestamps) - 1)
    )