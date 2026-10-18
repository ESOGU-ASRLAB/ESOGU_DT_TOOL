"""Stable, UI-independent HTTP contracts for external STLC integrations."""

from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.auth import require_api_key
from pipeline.pipeline_models import FileInfo, PipelineRunRequest, PipelineStepStatus, StepConfig, StepResult
from pipeline.step_adapters import (
    run_environment_setup,
    run_test_case_generation,
    run_test_case_optimization,
    run_test_code_generation,
    run_test_scenario_generation,
)
from services.artifact_service import ArtifactNotFoundError, ArtifactService
from services.execution_client import ExecutionAdapter, ExecutionRequest, create_execution_client
from services.job_service import JobNotFoundError, job_service
from services.monitoring_event_service import monitoring_event_service


router = APIRouter(
    prefix="/api/v1",
    tags=["external-integration"],
    dependencies=[Depends(require_api_key)],
)


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Any] = None
    job_id: Optional[str] = None


class ArtifactCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    type: str = Field("input", min_length=1, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactResponse(BaseModel):
    artifact_id: str
    name: str
    type: str
    metadata: Dict[str, Any]
    created_at: str


class JobAccepted(BaseModel):
    job_id: str
    status: str
    session_id: Optional[str] = None
    status_url: str
    result_url: str


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    correlation_id: Optional[str] = None
    status: str
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[Dict[str, Any]] = None


class JobResultResponse(BaseModel):
    job_id: str
    status: str
    result: Any


class GenerationBase(BaseModel):
    process_title: str = Field(..., min_length=1)
    artifact_ids: List[str] = Field(default_factory=list)
    model: Optional[str] = None
    api_key: Optional[str] = Field(
        None,
        description="Optional per-request model-provider key; prefer server-side MODEL_API_KEY.",
    )
    custom_prompt: Optional[str] = None
    session_id: Optional[str] = None


class ScenarioGenerationRequest(GenerationBase):
    test_type: str = "Functional"
    test_category: str = "Positive"


class EnvironmentSetupRequest(GenerationBase):
    environment_name: str = Field(..., min_length=1)


class ScenarioInput(BaseModel):
    ScenarioID: str = Field(..., min_length=1)
    Title: str = Field(..., min_length=1)
    Description: str = ""
    Objective: str = ""
    Category: str = ""

    class Config:
        extra = "allow"


class TestCaseGenerationRequest(GenerationBase):
    scenarios: List[ScenarioInput] = Field(default_factory=list)
    scenario_job_id: Optional[str] = None
    test_type: str = "Functional"


class TestCaseOptimizationRequest(GenerationBase):
    test_case_job_id: Optional[str] = Field(None, min_length=1)
    test_case_job_ids: List[str] = Field(default_factory=list)
    optimization_type: str = "individual"


class TestCodeGenerationRequest(GenerationBase):
    environment_session_id: Optional[str] = None
    optimization_job_id: Optional[str] = None
    environment_name: str = Field(..., min_length=1)
    output_format: str = "json"
    max_test_cases: Optional[int] = Field(None, gt=0)
    max_input_tokens: int = Field(64000, ge=4096, le=64000)


# Apply the structured error contract to every external route in OpenAPI.
router.responses.update({
    401: {"model": ErrorResponse, "description": "Missing or invalid API credentials"},
    404: {"model": ErrorResponse, "description": "Artifact or job not found"},
    409: {"model": ErrorResponse, "description": "Referenced job has not completed"},
    422: {"model": ErrorResponse, "description": "Validation or completed-job failure"},
    503: {"model": ErrorResponse, "description": "Optional external executor is not configured"},
    500: {"model": ErrorResponse, "description": "Unexpected backend failure"},
})


def _artifact_service() -> ArtifactService:
    return ArtifactService()


def _execution_client() -> ExecutionAdapter:
    return create_execution_client()


def _session_id(value: Optional[str], prefix: str) -> str:
    return value or f"{prefix}_{uuid.uuid4().hex}"


def _accepted(record: Dict[str, Any]) -> JobAccepted:
    job_id = record["job_id"]
    return JobAccepted(
        job_id=job_id,
        status=record["status"],
        session_id=record.get("correlation_id"),
        status_url=f"/api/v1/jobs/{job_id}",
        result_url=f"/api/v1/jobs/{job_id}/result",
    )


def _files(artifact_ids: List[str]) -> List[FileInfo]:
    try:
        return _artifact_service().as_file_info(artifact_ids)
    except ArtifactNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "ARTIFACT_NOT_FOUND",
                "message": "One or more input artifacts were not found.",
                "details": str(exc.args[0]),
            },
        ) from exc


def _unwrap(result: StepResult) -> Dict[str, Any]:
    if result.status != PipelineStepStatus.COMPLETED:
        raise RuntimeError(result.error or f"{result.step_id} failed")
    return result.output or {}


@router.post(
    "/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}},
)
async def create_artifact(request: ArtifactCreateRequest):
    await monitoring_event_service.emit_safely(
        "module.started", module="artifact_ingestion", status="running",
        metadata={"name": request.name, "type": request.type},
    )
    try:
        result = _artifact_service().create(
            name=request.name,
            content=request.content,
            artifact_type=request.type,
            metadata=request.metadata,
        )
    except Exception:
        await monitoring_event_service.emit_safely(
            "module.failed", module="artifact_ingestion", status="failed",
            error={"error_code": "ARTIFACT_INGESTION_FAILED", "message": "Artifact ingestion failed."},
        )
        raise
    await monitoring_event_service.emit_safely(
        "module.completed", module="artifact_ingestion", status="completed", progress=100,
        metrics={"artifact_count": 1}, metadata={"artifact_id": result.get("artifact_id")},
    )
    return result


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str):
    try:
        record = _artifact_service().get(artifact_id)
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail={
            "error_code": "ARTIFACT_NOT_FOUND",
            "message": "Input artifact was not found.",
            "details": artifact_id,
        }) from exc
    return {key: value for key, value in record.items() if key != "content"}


@router.post("/generations/scenarios", response_model=JobAccepted, status_code=202)
async def generate_scenarios(request: ScenarioGenerationRequest):
    session_id = _session_id(request.session_id, "scenario")
    req = PipelineRunRequest(
        session_id=session_id,
        selected_steps=["test-scenario-generation"],
        process_title=request.process_title,
        global_model=request.model,
        global_api_key=request.api_key,
        files={"test-scenario-generation": _files(request.artifact_ids)},
        step_configs={"test-scenario-generation": StepConfig(
            custom_prompt=request.custom_prompt,
            test_type=request.test_type,
            test_category=request.test_category,
            process_title=request.process_title,
        )},
    )

    async def operation():
        return _unwrap(await run_test_scenario_generation(req, {}))

    return _accepted(job_service.submit(
        "test_scenario_generation", operation(), correlation_id=session_id,
        monitoring_context={
            "module": "scenario_generation", "session_id": session_id,
            "process_title": request.process_title, "metadata": {"model": request.model},
        },
    ))


@router.post("/generations/environment", response_model=JobAccepted, status_code=202)
async def generate_environment(request: EnvironmentSetupRequest):
    session_id = _session_id(request.session_id, "environment")
    req = PipelineRunRequest(
        session_id=session_id,
        selected_steps=["environment-setup"],
        process_title=request.process_title,
        global_model=request.model,
        global_api_key=request.api_key,
        files={"environment-setup": _files(request.artifact_ids)},
        step_configs={"environment-setup": StepConfig(
            custom_prompt=request.custom_prompt,
            process_title=request.process_title,
            environment_name=request.environment_name,
        )},
    )

    async def operation():
        output = _unwrap(await run_environment_setup(req, {}))
        output.setdefault("session_id", session_id)
        return output

    return _accepted(job_service.submit(
        "environment_setup", operation(), correlation_id=session_id,
        monitoring_context={
            "module": "environment_setup", "session_id": session_id,
            "process_title": request.process_title, "metadata": {"model": request.model},
        },
    ))


def _scenarios_from_job(job_id: str) -> List[Dict[str, Any]]:
    try:
        source = job_service.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail={
            "error_code": "JOB_NOT_FOUND", "message": "Scenario job was not found.", "details": job_id
        }) from exc
    if source["status"] not in {"completed", "failed"}:
        raise HTTPException(status_code=409, detail={
            "error_code": "JOB_NOT_COMPLETE", "message": "Scenario job has not completed.", "details": job_id
        })
    if source["status"] == "failed":
        raise HTTPException(status_code=422, detail=source["error"])
    result = source.get("result") or {}
    scenario_data = result.get("test_scenarios", result)
    return scenario_data.get("TestScenarios", []) if isinstance(scenario_data, dict) else []


@router.post("/generations/test-cases", response_model=JobAccepted, status_code=202)
async def generate_test_cases(request: TestCaseGenerationRequest):
    if not request.scenarios and not request.scenario_job_id:
        raise HTTPException(status_code=422, detail={
            "error_code": "SCENARIOS_REQUIRED",
            "message": "Provide scenarios or scenario_job_id.",
            "details": None,
        })
    scenarios = (
        [
            item.model_dump() if hasattr(item, "model_dump") else item.dict()
            for item in request.scenarios
        ]
        if request.scenarios
        else _scenarios_from_job(request.scenario_job_id or "")
    )
    if not scenarios:
        raise HTTPException(status_code=422, detail={
            "error_code": "SCENARIOS_REQUIRED",
            "message": "The supplied source contains no test scenarios.",
            "details": None,
        })
    session_id = _session_id(request.session_id, "cases")
    req = PipelineRunRequest(
        session_id=session_id,
        selected_steps=["test-case-generation"],
        process_title=request.process_title,
        global_model=request.model,
        global_api_key=request.api_key,
        files={"test-case-generation": _files(request.artifact_ids)},
        step_configs={"test-case-generation": StepConfig(
            custom_prompt=request.custom_prompt,
            process_title=request.process_title,
            test_type=request.test_type,
        )},
    )
    previous = {"test-scenario-generation": StepResult(
        step_id="test-scenario-generation",
        status=PipelineStepStatus.COMPLETED,
        output={"test_scenarios": {"TestScenarios": scenarios}},
    )}

    async def operation():
        return _unwrap(await run_test_case_generation(req, previous))

    return _accepted(job_service.submit(
        "test_case_generation", operation(), correlation_id=session_id,
        monitoring_context={
            "module": "test_case_generation", "session_id": session_id,
            "process_title": request.process_title,
            "metadata": {"model": request.model, "scenario_count": len(scenarios)},
        },
    ))


def _test_cases_from_job(job_id: str) -> List[Dict[str, Any]]:
    try:
        source = job_service.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail={
            "error_code": "JOB_NOT_FOUND", "message": "Test-case job was not found.", "details": job_id
        }) from exc
    if source["status"] not in {"completed", "failed"}:
        raise HTTPException(status_code=409, detail={
            "error_code": "JOB_NOT_COMPLETE", "message": "Test-case job has not completed.", "details": job_id
        })
    if source["status"] == "failed":
        raise HTTPException(status_code=422, detail=source["error"])

    cases: List[Dict[str, Any]] = []
    result = source.get("result") or {}
    for scenario in result.get("test_case_results", []):
        if not isinstance(scenario, dict):
            continue
        cases.extend(
            case for case in scenario.get("test_cases", [])
            if isinstance(case, dict)
            and str(case.get("ExecutionStatus") or case.get("execution_status") or "").lower() != "unsupported"
            and not case.get("IsDiagnostic")
        )
    return cases


def _require_completed_job(job_id: str, expected_type: str) -> Dict[str, Any]:
    try:
        source = job_service.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail={
            "error_code": "JOB_NOT_FOUND", "message": "Referenced job was not found.", "details": job_id
        }) from exc
    if source.get("job_type") != expected_type:
        raise HTTPException(status_code=422, detail={
            "error_code": "JOB_TYPE_MISMATCH",
            "message": f"Expected a completed {expected_type} job.",
            "details": {"job_id": job_id, "job_type": source.get("job_type")},
        })
    if source["status"] not in {"completed", "failed"}:
        raise HTTPException(status_code=409, detail={
            "error_code": "JOB_NOT_COMPLETE", "message": "Referenced job has not completed.", "details": job_id
        })
    if source["status"] == "failed":
        raise HTTPException(status_code=422, detail=source["error"])
    return source


@router.post("/generations/test-case-optimization", response_model=JobAccepted, status_code=202)
async def optimize_test_cases(request: TestCaseOptimizationRequest):
    if request.optimization_type != "individual":
        raise HTTPException(status_code=422, detail={
            "error_code": "SERIAL_OPTIMIZATION_REQUIRED",
            "message": "This high-level endpoint requires optimization_type='individual'.",
            "details": request.optimization_type,
        })
    job_ids = list(dict.fromkeys(
        ([request.test_case_job_id] if request.test_case_job_id else [])
        + request.test_case_job_ids
    ))
    if not job_ids:
        raise HTTPException(status_code=422, detail={
            "error_code": "TEST_CASE_JOB_REQUIRED",
            "message": "Supply test_case_job_id or test_case_job_ids.",
            "details": None,
        })
    test_cases = []
    for job_id in job_ids:
        test_cases.extend(_test_cases_from_job(job_id))
    if not test_cases:
        raise HTTPException(status_code=422, detail={
            "error_code": "TEST_CASES_REQUIRED",
            "message": "The supplied job contains no executable test cases.",
            "details": job_ids,
        })

    session_id = _session_id(request.session_id, "optimization")
    req = PipelineRunRequest(
        session_id=session_id,
        selected_steps=["test-case-optimization"],
        process_title=request.process_title,
        global_model=request.model,
        global_api_key=request.api_key,
        step_configs={"test-case-optimization": StepConfig(
            custom_prompt=request.custom_prompt,
            process_title=request.process_title,
            process_name=request.process_title,
            optimization_type="individual",
        )},
    )
    previous = {"test-case-generation": StepResult(
        step_id="test-case-generation",
        status=PipelineStepStatus.COMPLETED,
        output={"test_case_results": [{"test_cases": test_cases}]},
    )}

    async def operation():
        return _unwrap(await run_test_case_optimization(req, previous))

    return _accepted(job_service.submit(
        "test_case_optimization", operation(), correlation_id=session_id,
        monitoring_context={
            "module": "test_case_optimization", "session_id": session_id,
            "process_title": request.process_title,
            "metadata": {
                "model": request.model,
                "optimization_type": "individual",
                "input_test_case_count": len(test_cases),
                "input_job_count": len(job_ids),
            },
        },
    ))


@router.post("/generations/test-code", response_model=JobAccepted, status_code=202)
async def generate_test_code(request: TestCodeGenerationRequest):
    if request.optimization_job_id:
        _require_completed_job(request.optimization_job_id, "test_case_optimization")
    session_id = _session_id(request.session_id, "code")
    req = PipelineRunRequest(
        session_id=session_id,
        selected_steps=["test-code-generation"],
        process_title=request.process_title,
        global_model=request.model,
        global_api_key=request.api_key,
        files={"test-code-generation": _files(request.artifact_ids)},
        step_configs={"test-code-generation": StepConfig(
            custom_prompt=request.custom_prompt,
            process_title=request.process_title,
            environment_session_id=request.environment_session_id,
            environment_name=request.environment_name,
            output_format=request.output_format,
            max_test_cases=request.max_test_cases,
            max_input_tokens=request.max_input_tokens,
        )},
    )

    async def operation():
        return _unwrap(await run_test_code_generation(req, {}))

    return _accepted(job_service.submit(
        "test_code_generation", operation(), correlation_id=session_id,
        monitoring_context={
            "module": "test_code_generation", "session_id": session_id,
            "process_title": request.process_title,
            "metadata": {
                "model": request.model,
                "environment_session_id": request.environment_session_id,
                "optimization_job_id": request.optimization_job_id,
                "max_input_tokens": request.max_input_tokens,
            },
        },
    ))


@router.post("/executions", response_model=JobAccepted, status_code=202)
async def submit_execution(request: ExecutionRequest):
    client = _execution_client()
    if not client.is_configured:
        raise HTTPException(status_code=503, detail={
            "error_code": "EXECUTION_SERVICE_NOT_CONFIGURED",
            "message": "The optional external execution service is not configured.",
            "details": (
                "Set EXECUTION_SERVICE_URL for HTTP execution, or set "
                "EXECUTION_ADAPTER=ssh_docker and SSH_EXECUTION_HOST for the ROS 2 harness."
            ),
        })

    async def operation():
        result = await client.submit(request)
        return result.model_dump() if hasattr(result, "model_dump") else result.dict()

    return _accepted(job_service.submit(
        "external_test_execution", operation(), correlation_id=request.session_id,
        monitoring_context={
            "module": "test_execution", "session_id": request.session_id,
            "process_id": request.process_id, "process_title": request.process_title,
            "metadata": {
                "language": request.language, "framework": request.framework,
                "test_case_id": request.test_case_id,
                "artifact_count": len(request.artifact_ids),
            },
        },
    ))


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str):
    try:
        record = job_service.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail={
            "error_code": "JOB_NOT_FOUND", "message": "Job was not found.", "details": job_id
        }) from exc
    record.pop("result", None)
    return record


@router.get("/jobs/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str):
    try:
        record = job_service.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail={
            "error_code": "JOB_NOT_FOUND", "message": "Job was not found.", "details": job_id
        }) from exc
    if record["status"] in {"pending", "running"}:
        raise HTTPException(status_code=202, detail={
            "error_code": "JOB_NOT_COMPLETE", "message": "Job is still running.", "job_id": job_id
        })
    if record["status"] == "failed":
        raise HTTPException(status_code=422, detail=record["error"])
    return {"job_id": job_id, "status": record["status"], "result": record["result"]}
