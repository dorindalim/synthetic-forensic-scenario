from app.schemas import (
    GeneratedScenario,
    ScenarioCreateRequest,
)

REQUIRED_ATTACK_CHAIN = (
    "authentication",
    "process_execution",
    "credential_access",
    "network_connection",
    "data_exfiltration",
)

class ScenarioInvariantError(Exception):
    # raised when a generated scenario does not meet the invariants
    pass

def _validateRequestedCounts(scenario: GeneratedScenario, config: ScenarioCreateRequest, errors: list[str]) -> None:
    # make sure the generated scenario has the requested number of users, devices and events
    if len(scenario.users) != config.users:
        errors.append(f"Expected {config.users} users, got {len(scenario.users)}")
    if len(scenario.devices) != config.devices:
        errors.append(f"Expected {config.devices} devices, got {len(scenario.devices)}")
    if len(scenario.events) != config.events:
        errors.append(f"Expected {config.events} events, got {len(scenario.events)}")
        
def _validateMetadata(scenario: GeneratedScenario, config: ScenarioCreateRequest, errors: list[str]) -> None:
    # make sure the generated scenario metadata matches the config
    metadata = scenario.metadata
    if metadata.scenario != config.scenario:
        errors.append(f"Expected scenario {config.scenario}, got {metadata.scenario}")
    if metadata.seed != config.seed:
        errors.append(f"Expected seed {config.seed}, got {metadata.seed}")
    if metadata.requestedUsers != config.users:
        errors.append(f"Expected requestedUsers {config.users}, got {metadata.requestedUsers}")
    if metadata.requestedDevices != config.devices:
        errors.append(f"Expected requestedDevices {config.devices}, got {metadata.requestedDevices}")
    if metadata.requestedEvents != config.events:
        errors.append(f"Expected requestedEvents {config.events}, got {metadata.requestedEvents}")