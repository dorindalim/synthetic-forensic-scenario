from fastapi import (
    BackgroundTasks,
    FastAPI,
    Request, 
    Response,
    status
)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.job_manager import ScenarioJobManager
from app.schemas import (
    ErrorResponse,
    HealthResponse,
    ScenarioCreateRequest,
    ScenarioJobResponse,
)

from app.store import (
    InMemoryScenarioStore,
    ScenarioJobRecord,
)

app = FastAPI(
    title="Synthetic Forensic Scenario Generator",
    description="A local REST API that generates deterministic synthetic credential-theft scenarios",
    version="1.0.0",
)

_scenarioStore = InMemoryScenarioStore()
_jobManager = ScenarioJobManager(_scenarioStore)

@app.exception_handler(RequestValidationError)
async def handleRequestValidationError(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    firstError = exception.errors()[0]

    if firstError["type"] == "json_invalid":
        message = "Request body has malformed JSON."
    else:
        fieldName = ".".join(
            str(part)
            for part in firstError["loc"]
            if part != "body"
        )

        message = firstError["msg"]

        if fieldName:
            message = f"{fieldName}: {message}"

    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_configuration",
            "message": message,
        },
    )

def _buildJobResponse(
    job: ScenarioJobRecord,
) -> ScenarioJobResponse:
    errorResponse: ErrorResponse | None = None

    if job.errorMessage is not None:
        errorResponse = ErrorResponse(
            error="generation_failed",
            message=job.errorMessage,
        )

    return ScenarioJobResponse(
        id=job.id,
        status=job.status,
        createdAt=job.createdAt,
        scenario=job.scenario,
        error=errorResponse,
    )

@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)    
def healthCheck() -> HealthResponse:
    return HealthResponse(status="ok")

@app.post(
    "/api/scenarios",
    response_model=ScenarioJobResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid scenario configuration.",
        }
    },
)

def createScenario(
    config: ScenarioCreateRequest,
    response: Response,
    backgroundTasks: BackgroundTasks,
) -> ScenarioJobResponse:
    job = _jobManager.createJob(config)
    backgroundTasks.add_task(_jobManager.runJob, job.id)
    
    response.headers["Location"] = f"/api/scenarios/{job.id}"
    
    return _buildJobResponse(job)

@app.get(
    "/api/scenarios/{jobId}",
    response_model=ScenarioJobResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Scenario ID not found.",
        }
    },
)
def getScenario(jobId: str) -> ScenarioJobResponse | JSONResponse:
    job = _scenarioStore.getJob(jobId)
    if job is None:
        errorResponse = ErrorResponse(
            error="scenario_not_found",
            message=f"Scenario ID '{jobId}' not found.",
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=errorResponse.model_dump(),
        )
    
    return _buildJobResponse(job)