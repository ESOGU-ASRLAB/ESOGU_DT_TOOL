"""
docker_execution_router.py
--------------------------
API Router for Docker-based test execution
Provides endpoints for containerized test execution including hardware simulations
"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from services.docker_executor import docker_executor
from services.parallel_docker_executor import parallel_docker_executor
from core.database import get_database
from datetime import datetime
import json

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/docker-execution",
    tags=["docker-execution"]
)

# Request Models
class DockerTestExecutionRequest(BaseModel):
    test_code: str
    language: str = "python"
    base_image: Optional[str] = None
    additional_packages: Optional[List[str]] = None
    environment_vars: Optional[Dict[str, str]] = None
    timeout: int = 300

class RobotSimulationRequest(BaseModel):
    test_code: str
    robot_type: str = "generic"  # generic, industrial, collaborative
    simulation_config: Optional[Dict[str, Any]] = None

class ProcessDockerExecutionRequest(BaseModel):
    process_name: str  # Test Code Generation process name
    language: str = "python"
    additional_packages: Optional[List[str]] = None
    environment_vars: Optional[Dict[str, str]] = None
    timeout: int = 300

class ImagePullRequest(BaseModel):
    image_name: str

# Response Models
class DockerExecutionResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: Optional[str] = None
    container_info: Optional[Dict[str, Any]] = None

class DockerStatusResponse(BaseModel):
    docker_available: bool
    optional: bool = True
    reason: Optional[str] = None
    images: List[str]
    container_status: Dict[str, Any]

@router.get("/status", response_model=DockerStatusResponse)
async def get_docker_status():
    """
    Get Docker environment status
    """
    try:
        availability = docker_executor.get_availability_status()
        available = availability["available"]
        images = docker_executor.list_available_images() if available else []
        container_status = docker_executor.get_container_status()
        
        return DockerStatusResponse(
            docker_available=available,
            optional=True,
            reason=availability.get("reason"),
            images=images,
            container_status=container_status
        )
    except Exception as e:
        # Docker is optional; its status endpoint must never make the main
        # application unhealthy.
        logger.info("Docker optional status check unavailable: %s", e)
        return DockerStatusResponse(
            docker_available=False,
            optional=True,
            reason=str(e),
            images=[],
            container_status={"available": False, "containers": []},
        )

@router.post("/execute", response_model=DockerExecutionResponse)
async def execute_test_in_docker(request: DockerTestExecutionRequest):
    """
    Execute test code in a Docker container
    
    This endpoint provides isolated test execution environment using Docker.
    Perfect for testing code that requires specific dependencies or system configurations.
    """
    try:
        if not docker_executor.is_available():
            raise HTTPException(
                status_code=503,
                detail="Docker is not available. Please ensure Docker is installed and running."
            )
        
        logger.info(f"🐳 Executing test in Docker container (language: {request.language})")
        
        result = await docker_executor.execute_test_in_container(
            test_code=request.test_code,
            language=request.language,
            base_image=request.base_image,
            additional_packages=request.additional_packages,
            environment_vars=request.environment_vars,
            timeout=request.timeout
        )
        
        # Save execution to database
        await save_docker_execution_result(
            execution_type="docker_test",
            request_data=request.dict(),
            result=result
        )
        
        return DockerExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"Docker execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-robot-simulation", response_model=DockerExecutionResponse)
async def execute_robot_simulation(request: RobotSimulationRequest):
    """
    Execute robot arm simulation tests
    
    Simulates robot arm movements and control logic in a containerized environment.
    Supports various robot types: generic (3-DOF), industrial (6-DOF), collaborative.
    
    Example test code:
    ```python
    # Test robot movement
    success, pos = robot.move_to_position([0.5, 0.3, 0.2])
    print(f"Position reached: {pos}")
    
    # Move to another position
    success, pos = robot.move_to_position([1.0, 0.5, 0.1])
    print(f"Final position: {pos}")
    ```
    """
    try:
        if not docker_executor.is_available():
            raise HTTPException(
                status_code=503,
                detail="Docker is not available. Please ensure Docker is installed and running."
            )
        
        logger.info(f"🤖 Executing robot arm simulation (type: {request.robot_type})")
        
        result = await docker_executor.execute_robot_arm_simulation(
            test_code=request.test_code,
            robot_type=request.robot_type,
            simulation_config=request.simulation_config
        )
        
        # Save execution to database
        await save_docker_execution_result(
            execution_type="robot_simulation",
            request_data=request.dict(),
            result=result
        )
        
        return DockerExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"Robot simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-from-process", response_model=DockerExecutionResponse)
async def execute_from_process(request: ProcessDockerExecutionRequest):
    """
    Execute test code from a Test Code Generation process in Docker
    
    Fetches test code from MongoDB and executes it in an isolated Docker container.
    """
    try:
        if not docker_executor.is_available():
            raise HTTPException(
                status_code=503,
                detail="Docker is not available. Please ensure Docker is installed and running."
            )
        
        # Fetch test code from database
        test_code = await fetch_test_code_by_process_name(request.process_name)
        
        logger.info(f"🐳 Executing process '{request.process_name}' in Docker container")
        
        result = await docker_executor.execute_test_in_container(
            test_code=test_code,
            language=request.language,
            additional_packages=request.additional_packages,
            environment_vars=request.environment_vars,
            timeout=request.timeout
        )
        
        # Save execution to database
        await save_docker_execution_result(
            execution_type="docker_process",
            request_data={
                "process_name": request.process_name,
                **request.dict()
            },
            result=result
        )
        
        return DockerExecutionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process Docker execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pull-image")
async def pull_docker_image(request: ImagePullRequest):
    """
    Pull a Docker image for test execution
    """
    try:
        if not docker_executor.is_available():
            raise HTTPException(
                status_code=503,
                detail="Docker is not available"
            )
        
        success = docker_executor.pull_image(request.image_name)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully pulled image: {request.image_name}"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to pull image: {request.image_name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image pull error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-robots")
async def get_available_robot_types():
    """
    Get list of available robot simulation types
    """
    return {
        "robot_types": [
            {
                "id": "generic",
                "name": "Generic 3-DOF Robot",
                "description": "Simple 3-axis robotic arm for basic operations",
                "dof": 3
            },
            {
                "id": "industrial",
                "name": "Industrial 6-DOF Robot",
                "description": "Industrial-grade 6-axis robotic arm for complex tasks",
                "dof": 6
            },
            {
                "id": "collaborative",
                "name": "Collaborative Robot",
                "description": "Safe collaborative robot for human-robot interaction",
                "dof": 4
            }
        ]
    }

@router.get("/supported-languages")
async def get_supported_languages():
    """
    Get list of supported programming languages for Docker execution
    """
    return {
        "languages": [
            {
                "id": "python",
                "name": "Python",
                "default_image": "python:3.9-slim",
                "extensions": [".py"]
            },
            {
                "id": "javascript",
                "name": "JavaScript",
                "default_image": "node:18-alpine",
                "extensions": [".js"]
            },
            {
                "id": "java",
                "name": "Java",
                "default_image": "openjdk:11-jre-slim",
                "extensions": [".java"]
            },
            {
                "id": "csharp",
                "name": "C#",
                "default_image": "mcr.microsoft.com/dotnet/sdk:6.0",
                "extensions": [".cs"]
            },
            {
                "id": "go",
                "name": "Go",
                "default_image": "golang:1.19-alpine",
                "extensions": [".go"]
            },
            {
                "id": "rust",
                "name": "Rust",
                "default_image": "rust:1.70-slim",
                "extensions": [".rs"]
            }
        ]
    }

# Helper Functions
async def fetch_test_code_by_process_name(process_name: str) -> str:
    """
    Fetch test code from MongoDB by code_generation_process_name
    """
    try:
        db = await get_database()
        collection = db["session_history"]
        
        # Find the most recent test code generation with matching process name
        session = await collection.find_one(
            {
                "processes.test_code_generation.process_name": process_name
            },
            sort=[("processes.test_code_generation.timestamp", -1)]
        )
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"No test code generation found for process: {process_name}"
            )
        
        # Extract test code from output
        test_code_gen = session.get("processes", {}).get("test_code_generation", {})
        output = test_code_gen.get("output", {})
        
        # Try multiple possible locations for test code
        test_code = None
        
        if isinstance(output, dict):
            test_code = output.get("test_code") or output.get("generated_code")
            
            if not test_code and "data" in output:
                data = output["data"]
                if isinstance(data, dict):
                    test_code = data.get("test_code") or data.get("generated_code")
        
        if not test_code:
            raise HTTPException(
                status_code=404,
                detail=f"No executable test code found for process: {process_name}"
            )
        
        logger.info(f"Successfully fetched test code for process: {process_name}")
        return test_code.strip()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching test code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def save_docker_execution_result(
    execution_type: str,
    request_data: Dict[str, Any],
    result: Dict[str, Any]
) -> str:
    """
    Save Docker execution result to database
    """
    try:
        db = await get_database()
        collection = db["session_history"]
        
        session_id = f"docker-exec-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "processes": {
                "docker_execution": {
                    "execution_type": execution_type,
                    "status": "completed" if result.get("success") else "failed",
                    "timestamp": datetime.now().isoformat(),
                    "input": request_data,
                    "output": result
                }
            }
        }
        
        await collection.insert_one(record)
        logger.info(f"✅ Saved Docker execution result: {session_id}")
        
        return session_id
        
    except Exception as e:
        logger.error(f"Failed to save Docker execution result: {str(e)}")
        return None

# ============================================================================
# PARALLEL DOCKER EXECUTION ENDPOINTS
# ============================================================================

class ParallelExecutionRequest(BaseModel):
    """Request model for parallel Docker execution"""
    process_name: str
    test_ids: List[str]
    language: str = "python"
    max_parallel: int = 5  # Maximum number of parallel containers
    timeout: int = 300
    additional_packages: Optional[List[str]] = None

class ParallelExecutionResponse(BaseModel):
    """Response model for parallel execution"""
    success: bool
    session_id: str
    message: str
    total_tests: int

class ExecutionProgressResponse(BaseModel):
    """Response model for execution progress"""
    session_id: str
    process_name: str
    status: str
    total_tests: int
    pending: int
    running: int
    completed: int
    failed: int
    success_rate: float
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    elapsed_time: float

class ExecutionResultsResponse(BaseModel):
    """Response model for detailed execution results"""
    session_id: str
    process_name: str
    status: str
    statistics: Dict[str, Any]
    execution_time: Dict[str, Any]
    jobs: List[Dict[str, Any]]

@router.post("/parallel/execute", response_model=ParallelExecutionResponse)
async def execute_parallel_tests(request: ParallelExecutionRequest):
    """
    Execute multiple tests in parallel Docker containers
    
    This endpoint creates a batch execution session and runs tests concurrently
    in isolated Docker containers. Perfect for running large test suites efficiently.
    
    Features:
    - Parallel execution with configurable concurrency
    - Real-time progress monitoring
    - Automatic resource management
    - Detailed per-test results
    """
    try:
        if not docker_executor.is_available():
            raise HTTPException(
                status_code=503,
                detail="Docker is not available. Please ensure Docker is installed and running."
            )
        
        if not request.test_ids:
            raise HTTPException(
                status_code=400,
                detail="No test IDs provided"
            )
        
        if request.max_parallel < 1 or request.max_parallel > 20:
            raise HTTPException(
                status_code=400,
                detail="max_parallel must be between 1 and 20"
            )
        
        logger.info(f"🚀 Creating parallel execution session for {len(request.test_ids)} tests")
        logger.info(f"📦 Config: {request.max_parallel} parallel containers, {request.timeout}s timeout")
        
        # Create batch session
        session_id = await parallel_docker_executor.create_batch_session(
            process_name=request.process_name,
            test_ids=request.test_ids,
            language=request.language,
            max_parallel=request.max_parallel,
            timeout=request.timeout,
            additional_packages=request.additional_packages
        )
        
        # Start execution in background (non-blocking)
        asyncio.create_task(parallel_docker_executor.execute_batch(session_id))
        
        return ParallelExecutionResponse(
            success=True,
            session_id=session_id,
            message=f"Parallel execution started for {len(request.test_ids)} tests",
            total_tests=len(request.test_ids)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parallel execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parallel/progress/{session_id}", response_model=ExecutionProgressResponse)
async def get_execution_progress(session_id: str):
    """
    Get real-time progress of a parallel execution session
    
    Use this endpoint to monitor the progress of running tests.
    Call this endpoint periodically (e.g., every 2 seconds) to get live updates.
    """
    try:
        progress = await parallel_docker_executor.get_session_progress(session_id)
        return ExecutionProgressResponse(**progress)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parallel/results/{session_id}", response_model=ExecutionResultsResponse)
async def get_execution_results(session_id: str):
    """
    Get detailed results of a parallel execution session
    
    Returns comprehensive results including:
    - Overall statistics (pass/fail counts, success rate)
    - Individual test results with output and errors
    - Execution timing information
    """
    try:
        results = await parallel_docker_executor.get_session_results(session_id)
        return ExecutionResultsResponse(**results)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parallel/cancel/{session_id}")
async def cancel_parallel_execution(session_id: str):
    """
    Cancel a running parallel execution session
    """
    try:
        await parallel_docker_executor.cancel_session(session_id)
        
        return {
            "success": True,
            "message": f"Session {session_id} cancelled",
            "session_id": session_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parallel/active-sessions")
async def get_active_sessions():
    """
    Get list of all active parallel execution sessions
    """
    try:
        sessions = []
        for session_id, session in parallel_docker_executor.active_sessions.items():
            progress = await parallel_docker_executor.get_session_progress(session_id)
            sessions.append(progress)
        
        return {
            "success": True,
            "count": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

