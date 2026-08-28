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
        
def _validateUniqueIds(scenario: GeneratedScenario, errors: list[str]) -> None:
    # make sure all users, devices and events have unique ids
    userIds = {user.id for user in scenario.users}
    if len(userIds) != len(scenario.users):
        errors.append("Duplicate user IDs found")
    
    deviceIds = {device.id for device in scenario.devices}
    if len(deviceIds) != len(scenario.devices):
        errors.append("Duplicate device IDs found")
    
    eventIds = {event.id for event in scenario.events}
    if len(eventIds) != len(scenario.events):
        errors.append("Duplicate event IDs found")
        
def _validateEvent(scenario: GeneratedScenario, errors: list[str]) -> None:
    # make sure all events have valid actor_user_id and device_id if they are not None
    userIds = {user.id for user in scenario.users}
    deviceIds = {device.id for device in scenario.devices}
    
    for event in scenario.events:
        if event.actor_user_id is not None and event.actor_user_id not in userIds:
            errors.append(f"Event {event.id} has invalid actor_user_id {event.actor_user_id}")
        if event.device_id is not None and event.device_id not in deviceIds:
            errors.append(f"Event {event.id} has invalid device_id {event.device_id}")
            
        # every attack must have both actor and device
        if event.type in REQUIRED_ATTACK_CHAIN:
            if event.actor_user_id is None:
                errors.append(f"Event {event.id} of type {event.type} must have an actor_user_id")
            if event.device_id is None:
                errors.append(f"Event {event.id} of type {event.type} must have a device_id")
        
        # event must have details field
        if not event.details:
            errors.append(f"Event {event.id} of type {event.type} must have details field")
            
def _validateEventTimestamps(scenario: GeneratedScenario, errors: list[str]) -> None:
    # make sure all events have timestamps in non-decreasing order
    for event in scenario.events:
        if event.timestamp.tzinfo is None or event.timestamp.tzinfo.utcoffset(event.timestamp) is None:
            errors.append(f"Event {event.id} of type {event.type} must have a timezone-aware timestamp")
    
    for i in range(len(scenario.events) - 1):
        currentEvent = scenario.events[i]
        nextEvent = scenario.events[i + 1]
        if currentEvent.timestamp > nextEvent.timestamp:
            errors.append(
                f"Event {currentEvent.id} occurs after event {nextEvent.id}."
            )

def _validateRequiredAttackChain(scenario: GeneratedScenario, errors: list[str]) -> None:
    # make sure the required attack chain is present in the events
    eventTypes = {event.type for event in scenario.events}
    for requiredEvent in REQUIRED_ATTACK_CHAIN:
        if requiredEvent not in eventTypes:
            errors.append(f"Missing required attack chain event: {requiredEvent}")
    
    # other bg events are allowed but the required attack chain must be in correct order
    requiredPosition = 0
    previousAttackTimestamp = None
    for event in scenario.events:
        if requiredPosition == len(REQUIRED_ATTACK_CHAIN):
            break
        expectedEvent = REQUIRED_ATTACK_CHAIN[requiredPosition]
        if event.type != expectedEvent:
            continue
        
        # make sure the required attack chain events are in correct order
        if previousAttackTimestamp is not None and event.timestamp <= previousAttackTimestamp:
            continue
        previousAttackTimestamp = event.timestamp
        requiredPosition += 1
    if requiredPosition != len(REQUIRED_ATTACK_CHAIN):
        errors.append("No complete chronological sequence of required attack chain events found in the scenario")
        
def validateScenarioInvariants(scenario: GeneratedScenario, config: ScenarioCreateRequest) -> list[str]:
    # make sure the generated scenario meets the invariants, return list of errors if any
    errors: list[str] = []
    
    _validateRequestedCounts(
        scenario=scenario,
        config=config,
        errors=errors
    )
    
    _validateMetadata(
        scenario=scenario,
        config=config,
        errors=errors
    )
    
    _validateUniqueIds(
        scenario=scenario,
        errors=errors
    )
    
    _validateEvent(
        scenario=scenario,
        errors=errors
    )
    
    _validateEventTimestamps(
        scenario=scenario,
        errors=errors
    )
    
    _validateRequiredAttackChain(
        scenario=scenario,
        errors=errors
    )   
    
    return errors

def assertScenarioInvariants(scenario: GeneratedScenario, config: ScenarioCreateRequest) -> None:
    # make sure the generated scenario meets the invariants, raise error if any
    errors = validateScenarioInvariants(scenario=scenario, config=config)
    if errors:
        message = "; ".join(errors)
        raise ScenarioInvariantError(message)