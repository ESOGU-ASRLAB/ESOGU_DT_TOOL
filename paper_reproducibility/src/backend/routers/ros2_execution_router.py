"""
ros2_execution_router.py
------------------------
API Router for ROS2 Docker-based test execution.

Bridges STLC Manager to a running stlc-robot-ros2:latest container.
No new containers are created – tests are injected via `docker exec`.

Endpoints
---------
GET  /api/ros2-execution/status
POST /api/ros2-execution/execute-single
POST /api/ros2-execution/execute-batch
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ros2_executor import ros2_executor
from core.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ros2-execution",
    tags=["ros2-execution"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ROS2SingleRequest(BaseModel):
    test_code: str
    test_id: str = "test"
    visual: bool = False
    timeout: int = 120


class ROS2BatchTestItem(BaseModel):
    test_id: str
    code: str


class ROS2BatchRequest(BaseModel):
    test_items: List[ROS2BatchTestItem]
    visual_count: int = 0          # first N tests run with GUI; rest are headless
    timeout: int = 120             # per-test timeout (seconds)


class ROS2ExecutionResult(BaseModel):
    test_id: str
    success: bool
    exit_code: int
    output: str
    error: Optional[str] = None
    visual: bool


class ROS2BatchResponse(BaseModel):
    results: List[ROS2ExecutionResult]
    total: int
    passed: int
    failed: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
async def get_ros2_status():
    """
    Return ROS2 container availability.

    The container must be started manually according to README_Docker.md Step 4:

        docker run --rm -it \\
          -e DISPLAY=<hostIp>:0.0 \\
          -e QT_X11_NO_MITSHM=1 \\
          stlc-robot-ros2:latest bash
    """
    status = ros2_executor.get_status()
    return status


@router.post("/execute-single", response_model=ROS2ExecutionResult)
async def execute_single(request: ROS2SingleRequest):
    """
    Execute a single Python test script inside the ROS2 container.

    - **visual=true**  → DISPLAY is forwarded; Gazebo/RViz windows will open.
    - **visual=false** → headless; no GUI windows.
    """
    if not ros2_executor.is_ros2_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "ROS2 container is not running. "
                "Start stlc-robot-ros2:latest first (README_Docker.md Step 4)."
            ),
        )

    logger.info(f"🦿 Single ROS2 execution: test_id={request.test_id} visual={request.visual}")

    result = await _run_single(request)

    await _save_result("ros2_single", {"test_id": request.test_id, "visual": request.visual}, result)

    return ROS2ExecutionResult(**result)


@router.post("/execute-batch", response_model=ROS2BatchResponse)
async def execute_batch(request: ROS2BatchRequest):
    """
    Execute multiple test scripts sequentially in the ROS2 container.

    **visual_count** – the first N tests run with DISPLAY forwarded (GUI visible).
    The remaining tests run headless (DISPLAY suppressed).

    Example: 100 tests, visual_count=25 → tests 1-25 show Gazebo, tests 26-100 run silently.
    """
    if not ros2_executor.is_ros2_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "ROS2 container is not running. "
                "Start stlc-robot-ros2:latest first (README_Docker.md Step 4)."
            ),
        )

    items = [item.dict() for item in request.test_items]
    logger.info(
        f"🦿 Batch ROS2 execution: {len(items)} tests, "
        f"visual_count={request.visual_count}, timeout={request.timeout}s"
    )

    results = await ros2_executor.execute_batch(
        test_items=items,
        visual_count=request.visual_count,
        timeout=request.timeout,
    )

    passed = sum(1 for r in results if r.get("success"))
    failed = len(results) - passed

    response = ROS2BatchResponse(
        results=[ROS2ExecutionResult(**r) for r in results],
        total=len(results),
        passed=passed,
        failed=failed,
    )

    await _save_result(
        "ros2_batch",
        {"test_count": len(items), "visual_count": request.visual_count},
        {"passed": passed, "failed": failed, "results": results},
    )

    return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _run_single(request: ROS2SingleRequest) -> Dict[str, Any]:
    """Thin wrapper so execute-single and batch share the same async path."""
    import asyncio

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: ros2_executor.execute_single(
            test_code=request.test_code,
            test_id=request.test_id,
            visual=request.visual,
            timeout=request.timeout,
        ),
    )
    return result


async def _save_result(execution_type: str, request_data: dict, result: Any):
    """Persist execution results to MongoDB (best-effort)."""
    try:
        db = await get_database()
        await db["ros2_execution_history"].insert_one(
            {
                "execution_type": execution_type,
                "request_data": request_data,
                "result": result if isinstance(result, dict) else str(result),
                "created_at": datetime.utcnow(),
            }
        )
    except Exception as exc:
        logger.warning(f"Could not save ROS2 execution result to DB: {exc}")
