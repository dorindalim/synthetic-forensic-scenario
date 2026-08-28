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
    