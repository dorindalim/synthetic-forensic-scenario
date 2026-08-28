## 1. Prerequisites and dependency installation

### Prerequisites

- Python 3.11 or later
- `pip`
- A terminal

The application has been tested using Python 3.13.7.


### Clone the repository

```bash
git clone https://github.com/dorindalim/synthetic-forensic-scenario.git
cd synthetic-forensic-scenario
```

### Create a virtual environment

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate
```

### Install runtime dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Install test dependencies

```bash
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` also installs the dependencies from `requirements.txt`.

## 2. Running the service locally

Run this command from the repo root:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

The service will be available at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```


Keep the Uvicorn terminal open while testing the API. Open a second terminal and navigate to the repository root before running the `curl` commands. If necessary, reactivate the virtual environment in the second terminal.

Run all API test commands in the second terminal. When testing is complete, return to the Uvicorn terminal and press `Ctrl+C` to stop the service.

### Quick health check

```bash
curl -i http://127.0.0.1:8000/health
```

Expected response:

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{
  "status": "ok"
}
```

## 3. Running automated tests

Run the complete test suite from the repository root:

```bash
python -m pytest -v
```
### Test files overview

- `tests/conftest.py` provides shared fixtures for the API client, valid request data, validated configuration, and generated scenario. It contains setup rather than test cases.

- `tests/test_generator.py` tests deterministic generation, requested counts, metadata, unique IDs, valid references, timestamps, and the required credential-theft attack chain.

- `tests/test_invariants.py` tests that valid scenarios pass validation and that incorrect counts, duplicate IDs, invalid references, unsorted timestamps, and missing attack stages are detected.

- `tests/test_job_manager.py` tests successful job-status transitions from `pending` to `running` to `completed`, as well as failure handling.

- `tests/test_api.py` tests the health, scenario-submission, and scenario-retrieval endpoints, together with invalid-request and not-found responses.

The current test files contains 36 tests covering:

- Service health
- Successful scenario submission
- Completed scenario retrieval
- Invalid configurations
- Missing required fields
- Unsupported scenario types
- Unexpected configuration fields
- Malformed JSON
- Unknown scenario IDs
- Fixed-seed generation
- Equivalent output for equivalent configurations and seeds
- Different output for different seeds
- Requested user, device and event counts
- Unique identifiers
- Entity-reference integrity
- Valid and ordered timestamps
- Required attack-event types
- Attack-chain ordering
- Independent invariant validation
- Successful asynchronous status transitions
- Generation-failure handling

To stop after a failure:

```bash
python -m pytest -x -v
```

To run one specific test file:

```bash
python -m pytest tests/test_api.py -v
```

The current verified result is:

```text
36 passed
```

## 4. API documentation

### `GET /health`

Checks whether the service is available.

#### Example request

```bash
curl -i http://127.0.0.1:8000/health
```

#### Successful response

Status:

```http
200 OK
```

Body:

```json
{
  "status": "ok"
}
```

---

### `POST /api/scenarios`

Validates a scenario configuration and starts asynchronous generation.

#### Request fields

| Field | Type | Required | Validation |
|---|---:|---:|---|
| `scenario` | string | Yes | Must be `credential_theft` |
| `users` | integer | Yes | Must be at least 1 |
| `devices` | integer | Yes | Must be at least 1 |
| `events` | integer | Yes | Must be at least 5 |
| `seed` | integer | Yes | Used for deterministic generation |

Unknown fields are rejected.

The `events` value is the total number of events, including the five required attack-chain events and any background events.

#### Example request

```bash
curl -i \
  -X POST \
  http://127.0.0.1:8000/api/scenarios \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "credential_theft",
    "users": 2,
    "devices": 2,
    "events": 25,
    "seed": 42
  }'
```

#### Successful response

Status:

```http
202 Accepted
```

Headers include:

```http
Location: /api/scenarios/scenario-1ab67ce9f426
```

Example body:

```json
{
  "id": "scenario-1ab67ce9f426",
  "status": "pending",
  "created_at": "2026-08-26T05:24:40.986507Z"
}
```

The exact scenario ID and creation timestamp will differ between requests.

---

### `GET /api/scenarios/{scenario_id}`

Supported statuses are:

- `pending`
- `running`
- `completed`
- `failed`

#### Example request

```bash
curl -s \
  http://127.0.0.1:8000/api/scenarios/scenario-1ab67ce9f426 \
  | python -m json.tool
```

#### Pending or running response

Status:

```http
200 OK
```

Example body:

```json
{
  "id": "scenario-1ab67ce9f426",
  "status": "running",
  "created_at": "2026-08-26T05:24:40.986507Z"
}
```

Because local generation is fast, a client may retrieve a scenario after it has already reached `completed`.

#### Completed response

Status:

```http
200 OK
```

Example body:

```json
{
  "id": "scenario-1ab67ce9f426",
  "status": "completed",
  "created_at": "2026-08-26T05:24:40.986507Z",
  "scenario": {
    "metadata": {
      "scenario": "credential_theft",
      "seed": 42,
      "requestedUsers": 2,
      "requestedDevices": 2,
      "requestedEvents": 5
    },
    "users": [
      {
        "id": "user-000",
        "username": "Alice",
        "role": "Employee"
      },
      {
        "id": "user-001",
        "username": "Benjamin",
        "role": "Employee"
      }
    ],
    "devices": [
      {
        "id": "device-000",
        "hostname": "DESKTOP-001",
        "os": "macOS"
      },
      {
        "id": "device-001",
        "hostname": "WORKSTATION-002",
        "os": "Windows 10"
      }
    ],
    "events": [
      {
        "id": "event-001",
        "type": "authentication",
        "timestamp": "2025-03-13T23:07:00Z",
        "actor_user_id": "user-000",
        "device_id": "device-001",
        "details": {
          "result": "success",
          "method": "password",
          "source_ip": "198.51.100.130"
        }
      },
      {
        "id": "event-002",
        "type": "process_execution",
        "timestamp": "2025-03-13T23:08:00Z",
        "actor_user_id": "user-000",
        "device_id": "device-001",
        "details": {
          "process_name": "explorer.exe",
          "parent_process": "explorer.exe",
          "process_id": 1434
        }
      },
      {
        "id": "event-003",
        "type": "credential_access",
        "timestamp": "2025-03-13T23:09:00Z",
        "actor_user_id": "user-000",
        "device_id": "device-001",
        "details": {
          "method": "memory_credentials",
          "target": "local_user_credentials"
        }
      },
      {
        "id": "event-004",
        "type": "network_connection",
        "timestamp": "2025-03-13T23:11:00Z",
        "actor_user_id": "user-000",
        "device_id": "device-001",
        "details": {
          "destination_ip": "203.0.113.51",
          "destination_port": 443,
          "protocol": "tcp"
        }
      },
      {
        "id": "event-005",
        "type": "data_exfiltration",
        "timestamp": "2025-03-13T23:13:00Z",
        "actor_user_id": "user-000",
        "device_id": "device-001",
        "details": {
          "channel": "https",
          "data_type": "credential_archive",
          "bytes_transferred": 4621300
        }
      }
    ]
  }
}
```

The generated values depend on the complete configuration and seed. The response above shows the response schema.

#### Failed response

If generation encounters an unexpected error, the job remains retrievable with `failed` status.

```json
{
  "id": "scenario-1ab67ce9f426",
  "status": "failed",
  "created_at": "2026-08-26T05:24:40.986507Z",
  "error": {
    "error": "generation_failed",
    "message": "Scenario generation failed"
  }
}
```

### Error responses

Errors use a consistent JSON structure:

```json
{
  "error": "error_code",
  "message": "Explanation"
}
```

#### Invalid event count

```http
400 Bad Request
```

```json
{
  "error": "invalid_configuration",
  "message": "events: Input should be greater than or equal to 5"
}
```

#### Missing required field

```http
400 Bad Request
```

```json
{
  "error": "invalid_configuration",
  "message": "seed: Field required"
}
```

#### Malformed JSON

```http
400 Bad Request
```

```json
{
  "error": "invalid_configuration",
  "message": "Request body has malformed JSON."
}
```

#### Unknown scenario ID

```http
404 Not Found
```

```json
{
  "error": "scenario_not_found",
  "message": "Scenario ID 'does-not-exist' not found."
}
```

## 5. Data model

### Scenario configuration

| Field | Description |
|---|---|
| `scenario` | Requested incident type |
| `users` | Exact number of users to generate |
| `devices` | Exact number of devices to generate |
| `events` | Exact total number of events to generate |
| `seed` | Integer controlling deterministic choices |

### Scenario job

| Field | Description |
|---|---|
| `id` | Non-deterministic job identifier |
| `status` | `pending`, `running`, `completed` or `failed` |
| `created_at` | Non-deterministic job creation timestamp |
| `scenario` | Generated data, present when completed |
| `error` | Failure information, present when failed |

The original validated configuration is retained internally while the job is being processed.

### Scenario metadata

| Field | Description |
|---|---|
| `scenario` | Generated scenario type |
| `seed` | Seed used during generation |
| `requestedUsers` | Requested user count |
| `requestedDevices` | Requested device count |
| `requestedEvents` | Requested total event count |

### User

| Field | Description |
|---|---|
| `id` | Unique synthetic user ID |
| `username` | Synthetic username |
| `role` | Synthetic organisational role |

### Device

| Field | Description |
|---|---|
| `id` | Unique synthetic device ID |
| `hostname` | Synthetic hostname |
| `os` | Synthetic operating system |

### Event

| Field | Description |
|---|---|
| `id` | Unique event ID |
| `type` | Forensic event type |
| `timestamp` | Timezone-aware ISO 8601 timestamp |
| `actor_user_id` | Referenced user ID, where applicable |
| `device_id` | Referenced device ID, where applicable |
| `details` | Event-specific context |

The required event types are:

1. `authentication`
2. `process_execution`
3. `credential_access`
4. `network_connection`
5. `data_exfiltration`

Additional background event types may include normal file access, DNS queries, system-service events and user activity.

## 6. Deterministic generation

Scenario content is generated using a local instance of Python's seeded random-number generator:

```python
rng = random.Random(config.seed)
```

Determinism is done by:

1. Creating a new local random generator for every request.
2. Seeding it with the client-provided `seed`.
3. Generating users, devices and events in a stable order.
4. Deriving the synthetic base timestamp from the seeded generator instead of the current time.
5. Creating the five required attack events in a fixed logical order.
6. Sorting all required and background events chronologically.
7. Assigning event IDs after chronological sorting.
8. Validating the completed scenario before marking the job as completed.

Two requests with equivalent configurations and seeds produce equivalent:

- Users
- Devices
- Events
- Event details
- Entity references
- Synthetic timestamps

These fields are intentionally non-deterministic:

- Scenario job ID
- Job creation timestamp
- Exact processing time

These fields identify and track an API operation and do not form part of the deterministic scenario content.

## 7. Asynchronous generation

`POST /api/scenarios` does not wait for generation to finish.

The request flow is:

1. FastAPI and Pydantic validate the JSON configuration.
2. A job is created in the in-memory store with `pending` status.
3. The API returns `202 Accepted` with a scenario ID and `Location` header.
4. FastAPI runs the generation operation as a background task.
5. The job changes to `running`.
6. Users, devices and events are generated.
7. The independent invariant validator checks the completed scenario.
8. A valid job changes to `completed` and stores its scenario.
9. An exception changes the job to `failed` and records failure information.

## 8. Storage choice and limitations

The application uses a thread-safe in-memory store.

Scenario jobs are stored in a Python dictionary and protected with a lock while jobs are read or updated.

### Advantages

- No external database is required.
- Setup remains small and local.
- Reads and writes are fast.
- The implementation is easy to understand and test.
- It satisfies retrieval for the lifetime of the application.

### Limitations

- All jobs are lost when the application stops or restarts.
- Jobs are not shared between multiple application processes or servers.
- Memory usage grows as scenarios are created.
- There is no automatic expiration or removal of old jobs.
- The store is not suitable for distributed deployment.

## 9. Important design decisions and trade-offs

### FastAPI and Pydantic

FastAPI provides concise routing, response models, automatic OpenAPI documentation and integration with Pydantic validation. There is strict request validation rejects incorrect types, missing fields and unexpected configuration fields.

However, the application depends on framework-specific models and validation behaviour.

### In-memory storage

An in-memory store was chosen instead of SQLite or a remote database to keep local setup focused on the assessed API and generation logic.

The trade-off is loss of data on restart and lack of multi-process support.

### Framework background tasks

FastAPI background tasks were chosen to keep the application self-contained and allows background generation to share the in-memory store.

The trade-off is that jobs are not durable and cannot continue after process termination.

### Independent invariant validation

Scenario validation is implemented separately from scenario generation to avoid assuming that generator output is automatically correct. The same invariants can then be tested independently using deliberately invalid scenarios.

The trade-off is some duplication between generation assumptions and validation rules.

### Required and background events

The five mandatory attack events are created first with strictly increasing timestamps. Background events are then added until the requested total is reached.

Background event types are kept separate from the required types to make the intended attack chain clear.

### Deterministic scenario data and non-deterministic job metadata

Generated scenario content is deterministic, while job IDs and creation timestamps are not.

This allows clients to submit and track separate jobs without making it harder to generate the same forensic data again.

## 10. Known limitations and production improvements

### Data storage

Current limitation:

- Jobs and scenarios are stored in memory and are lost when the application stops.

Production improvement:

- Store jobs and generated scenarios in PostgreSQL or another persistent database.

### Multiple application workers

Current limitation:

- Each process would have its own independent in-memory store.

Production improvement:

- Used a shared DB and job queue so all processes can access the same jobs.

### Resource limits

Current limitation:

- Minimum values are checked, but there are no maximum values. Large requests may use too much memory or take too long.

Production improvement:

- Set a maximum value for users, devices and events.
- Add request-size, timeout and rate limits.

### Job retention

Current limitation:

- Completed and failed jobs remain in memory until the app stops.

Production improvement:

- Automatically remove old jobs after a certain period.

### API security

Current limitation:

- The local API does not require authentication or authorisation.

Production improvement:

- Add authentication, access control, rate limiting and audit logging if exposed outside a trusted local environment.

### Error reporting

Current limitation:

- Information about generation failures is stored with the job.

Production improvement:

- Record the detailed errors in application logs while showing clients a safe and simple error msg.
- Add correlation IDs and monitoring.

### Supported scenarios

Current limitation:

- Only `credential_theft` is supported.

Production improvement:

- Add more incident types and allow different attack stages to be configured.

### Large-scenario retrieval

Current limitation:

- A completed scenario is returned as one response.

Production improvement:

- Add pagination and a separate event-retrieval endpoint for large scenarios.

### Cancellation and progress

Current limitation:

- Jobs cannot be cancelled and do not report percentage progress.

Production improvement:

- Add cancellation, progress information and execution deadlines.

## Project structure

```text
synthetic-forensic-scenario-generator/
├── app/
│   ├── __init__.py
│   ├── generator.py
│   ├── invariants.py
│   ├── job_manager.py
│   ├── main.py
│   ├── schemas.py
│   └── store.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_generator.py
│   ├── test_invariants.py
│   └── test_job_manager.py
├── .gitignore
├── AI_USAGE.md
├── pytest.ini
├── README.md
├── requirements.txt
└── requirements-dev.txt
```