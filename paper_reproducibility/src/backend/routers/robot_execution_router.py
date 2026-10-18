"""
Robot Test Execution API Router
Endpoints for executing ROS 2 robot tests with Docker containers
Supports hybrid execution: headless batch + GUI visualization
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import asyncio
import uuid
from datetime import datetime
import logging

from models.robot_test_criteria import (
    BatchTestExecutionRequest,
    BatchTestExecutionResponse,
    TestExecutionResult
)
from services.robot_docker_executor import RobotDockerExecutor

router = APIRouter(prefix="/api/robot-execution", tags=["Robot Test Execution"])
logger = logging.getLogger(__name__)

# Global executor instance
robot_executor = RobotDockerExecutor()

# Track execution sessions
execution_sessions: Dict[str, Dict[str, Any]] = {}


@router.get("/health")
async def health_check():
    """Check if Robot Docker executor is available"""
    return {
        "status": "healthy" if robot_executor.is_available else "unavailable",
        "docker_available": robot_executor.is_available,
        "message": "Robot test executor ready" if robot_executor.is_available else "Docker not available"
    }


@router.post("/execute-batch", response_model=BatchTestExecutionResponse)
async def execute_batch_tests(
    request: BatchTestExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute batch of robot tests with hybrid execution:
    - Headless tests run in parallel (bulk processing)
    - One visual test runs in Gazebo GUI (if specified)
    
    Example request:
    {
        "process_name": "Robot Joint Movement Tests",
        "test_ids": ["TC_001", "TC_002", "TC_003"],
        "max_parallel": 5,
        "visual_test_id": "TC_001",
        "enable_gazebo_recording": true
    }
    """
    
    if not robot_executor.is_available:
        raise HTTPException(
            status_code=503,
            detail="Docker is not available. Please ensure Docker Desktop is running."
        )
    
    if not request.test_ids:
        raise HTTPException(
            status_code=400,
            detail="test_ids cannot be empty"
        )
    
    # Generate unique session ID
    session_id = f"robot-batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    # Initialize session tracking
    execution_sessions[session_id] = {
        "session_id": session_id,
        "status": "initiated",
        "request": request.dict(),
        "total_tests": len(request.test_ids),
        "completed_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "error_tests": 0,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "results": []
    }
    
    # Calculate estimated duration (rough estimate)
    headless_count = len(request.test_ids) - (1 if request.visual_test_id else 0)
    visual_count = 1 if request.visual_test_id else 0
    
    # Estimate: headless takes ~30s per batch, visual takes ~60s
    estimated_duration = (headless_count * 30 / request.max_parallel) + (visual_count * 60)
    
    # Start execution in background
    background_tasks.add_task(
        execute_batch_background,
        session_id,
        request
    )
    
    logger.info(f"🚀 Robot batch execution initiated: {session_id}")
    
    return BatchTestExecutionResponse(
        session_id=session_id,
        message=f"Robot test batch execution started with {len(request.test_ids)} tests",
        total_tests=len(request.test_ids),
        headless_tests=headless_count,
        visual_tests=visual_count,
        estimated_duration=estimated_duration,
        status="initiated"
    )


async def execute_batch_background(session_id: str, request: BatchTestExecutionRequest):
    """Background task for batch execution"""
    try:
        execution_sessions[session_id]["status"] = "running"
        
        # Execute batch
        result = await robot_executor.execute_batch_tests(request, session_id)
        
        # Check if execution was successful
        if result.get("success") is False:
            # Execution failed (e.g., no test cases found)
            execution_sessions[session_id].update({
                "status": "failed",
                "error": result.get("error", "Unknown error"),
                "end_time": datetime.now().isoformat()
            })
            logger.error(f"❌ Robot batch execution failed: {session_id} - {result.get('error')}")
            return
        
        # Update session with successful result
        execution_sessions[session_id].update({
            "status": "completed",
            "completed_tests": result.get("total_tests", 0),
            "passed_tests": result.get("passed", 0),
            "failed_tests": result.get("failed", 0),
            "error_tests": result.get("errors", 0),
            "end_time": datetime.now().isoformat(),
            "results": result.get("results", [])
        })
        
        logger.info(f"✅ Robot batch execution completed: {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Robot batch execution failed: {session_id} - {e}")
        execution_sessions[session_id].update({
            "status": "failed",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })


@router.get("/progress/{session_id}")
async def get_execution_progress(session_id: str):
    """
    Get real-time progress of robot test execution
    
    Response:
    {
        "session_id": "robot-batch-20260723-...",
        "status": "running",
        "total_tests": 10,
        "completed_tests": 5,
        "passed_tests": 4,
        "failed_tests": 1,
        "progress_percentage": 50.0
    }
    """
    
    if session_id not in execution_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    session = execution_sessions[session_id]
    
    # Calculate progress
    progress_percentage = 0.0
    if session["total_tests"] > 0:
        progress_percentage = (session["completed_tests"] / session["total_tests"]) * 100
    
    return {
        "session_id": session_id,
        "status": session["status"],
        "total_tests": session["total_tests"],
        "completed_tests": session["completed_tests"],
        "passed_tests": session["passed_tests"],
        "failed_tests": session["failed_tests"],
        "error_tests": session["error_tests"],
        "progress_percentage": round(progress_percentage, 2),
        "start_time": session["start_time"],
        "end_time": session.get("end_time"),
        "error": session.get("error")
    }


@router.get("/results/{session_id}")
async def get_execution_results(session_id: str):
    """
    Get detailed results of robot test execution
    
    Returns:
    - Complete test results with validation details
    - Per-test PASS/FAIL status
    - Validation check results (position, timing, collision, ROS 2 health)
    - Container logs and error messages
    """
    
    if session_id not in execution_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    session = execution_sessions[session_id]
    
    if session["status"] not in ["completed", "failed"]:
        return {
            "session_id": session_id,
            "status": session["status"],
            "message": "Execution still in progress. Use /progress endpoint for status.",
            "completed": False
        }
    
    return {
        "session_id": session_id,
        "status": session["status"],
        "completed": True,
        "request": session["request"],
        "summary": {
            "total_tests": session["total_tests"],
            "completed_tests": session["completed_tests"],
            "passed_tests": session["passed_tests"],
            "failed_tests": session["failed_tests"],
            "error_tests": session["error_tests"],
            "success_rate": round(
                (session["passed_tests"] / session["completed_tests"] * 100)
                if session["completed_tests"] > 0 else 0.0,
                2
            )
        },
        "timing": {
            "start_time": session["start_time"],
            "end_time": session.get("end_time"),
        },
        "results": session["results"],
        "error": session.get("error")
    }


@router.get("/sessions")
async def list_execution_sessions():
    """
    List all robot test execution sessions
    
    Returns:
    - All tracked execution sessions
    - Session summaries with status and results
    """
    
    sessions_summary = []
    
    for session_id, session in execution_sessions.items():
        sessions_summary.append({
            "session_id": session_id,
            "status": session["status"],
            "total_tests": session["total_tests"],
            "completed_tests": session["completed_tests"],
            "passed_tests": session["passed_tests"],
            "failed_tests": session["failed_tests"],
            "start_time": session["start_time"],
            "end_time": session.get("end_time")
        })
    
    return {
        "total_sessions": len(sessions_summary),
        "sessions": sessions_summary
    }


@router.delete("/sessions/{session_id}")
async def delete_execution_session(session_id: str):
    """Delete a tracked execution session"""
    
    if session_id not in execution_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    del execution_sessions[session_id]
    
    return {
        "success": True,
        "message": f"Session {session_id} deleted"
    }


@router.get("/gazebo-status")
async def get_gazebo_status():
    """
    Check if Gazebo visualization is currently running
    
    Returns:
    - Status of GUI containers
    - Current visual test (if any)
    """
    
    # Check for running GUI containers
    try:
        import docker
        client = docker.from_env()
        
        containers = client.containers.list(filters={
            "ancestor": "stlc-robot-ros2:latest",
            "status": "running"
        })
        
        gui_containers = []
        for container in containers:
            env_vars = container.attrs.get("Config", {}).get("Env", [])
            is_gui = any("DISPLAY=:0" in env for env in env_vars)
            
            if is_gui:
                gui_containers.append({
                    "container_id": container.short_id,
                    "name": container.name,
                    "status": container.status
                })
        
        return {
            "gazebo_running": len(gui_containers) > 0,
            "gui_containers": gui_containers,
            "count": len(gui_containers)
        }
        
    except Exception as e:
        logger.error(f"Error checking Gazebo status: {e}")
        return {
            "gazebo_running": False,
            "error": str(e)
        }
