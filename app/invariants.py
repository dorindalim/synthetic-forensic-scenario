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