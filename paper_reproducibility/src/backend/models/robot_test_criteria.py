"""
Robot Test Criteria Models
Defines measurable criteria for ROS 2 robot test PASS/FAIL decisions
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TestResult(str, Enum):
    """Test execution result"""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class PositionCriteria(BaseModel):
    """Position accuracy criteria"""
    target_joint_angles: List[float] = Field(
        ...,
        description="Target joint angles in radians (must match robot DOF)"
    )
    position_tolerance: float = Field(
        default=0.01,
        description="Maximum allowed position error (radians for joints, meters for Cartesian)"
    )
    check_type: str = Field(
        default="joint_space",
        description="'joint_space' or 'cartesian'"
    )
    
    # Optional Cartesian position
    target_cartesian_position: Optional[List[float]] = Field(
        default=None,
        description="[x, y, z] target position in meters"
    )
    target_cartesian_orientation: Optional[List[float]] = Field(
        default=None,
        description="[qx, qy, qz, qw] target orientation quaternion"
    )


class TimingCriteria(BaseModel):
    """Timing and performance criteria"""
    max_duration: float = Field(
        default=30.0,
        description="Maximum allowed execution time in seconds"
    )
    min_duration: Optional[float] = Field(
        default=None,
        description="Minimum expected execution time (detect too-fast/skipped movements)"
    )
    check_timeout: bool = Field(
        default=True,
        description="Fail test if duration exceeds max_duration"
    )


class CollisionCriteria(BaseModel):
    """Collision detection criteria"""
    allow_self_collision: bool = Field(
        default=False,
        description="Allow robot self-collision"
    )
    allow_environment_collision: bool = Field(
        default=False,
        description="Allow collision with environment objects"
    )
    check_collisions: bool = Field(
        default=True,
        description="Enable collision checking"
    )


class ROS2HealthCriteria(BaseModel):
    """ROS 2 system health criteria"""
    required_nodes: List[str] = Field(
        default=[
            "/move_group",
            "/robot_state_publisher",
            "/joint_state_publisher"
        ],
        description="ROS 2 nodes that must be running"
    )
    required_topics: List[str] = Field(
        default=[
            "/joint_states",
            "/robot_description",
            "/move_group/display_planned_path"
        ],
        description="ROS 2 topics that must be active"
    )
    check_node_health: bool = Field(
        default=True,
        description="Verify ROS 2 nodes are running"
    )


class TrajectoryValidationCriteria(BaseModel):
    """Trajectory validation criteria"""
    max_joint_velocity: Optional[float] = Field(
        default=None,
        description="Maximum allowed joint velocity (rad/s)"
    )
    max_joint_acceleration: Optional[float] = Field(
        default=None,
        description="Maximum allowed joint acceleration (rad/s²)"
    )
    check_trajectory_smoothness: bool = Field(
        default=False,
        description="Check for smooth trajectory (no sudden jumps)"
    )
    trajectory_smoothness_threshold: float = Field(
        default=0.1,
        description="Maximum allowed trajectory discontinuity"
    )


class RobotTestCriteria(BaseModel):
    """
    Complete test criteria for robot arm tests
    Defines all measurable criteria for PASS/FAIL decision
    """
    
    # Test identification
    test_case_id: str = Field(..., description="Unique test case identifier")
    test_name: str = Field(..., description="Human-readable test name")
    
    # Validation criteria
    position_criteria: PositionCriteria
    timing_criteria: TimingCriteria = Field(default_factory=TimingCriteria)
    collision_criteria: CollisionCriteria = Field(default_factory=CollisionCriteria)
    ros2_health_criteria: ROS2HealthCriteria = Field(default_factory=ROS2HealthCriteria)
    trajectory_validation: Optional[TrajectoryValidationCriteria] = None
    
    # Execution settings
    robot_type: str = Field(default="ur10e", description="Robot type (ur5, ur10e, etc.)")
    planning_attempts: int = Field(default=10, description="MoveIt planning attempts")
    planning_time: float = Field(default=10.0, description="MoveIt planning time limit")
    
    # Visual debugging
    enable_visualization: bool = Field(
        default=False,
        description="Run this test in Gazebo GUI mode for visual debugging"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_case_id": "TC_001",
                "test_name": "Move to home position",
                "position_criteria": {
                    "target_joint_angles": [1.0, 0.0, -1.57, 0.0, -1.57, 0.0, 0.0],
                    "position_tolerance": 0.01,
                    "check_type": "joint_space"
                },
                "timing_criteria": {
                    "max_duration": 30.0
                },
                "enable_visualization": False
            }
        }


class ValidationResult(BaseModel):
    """Result of a single validation check"""
    check_name: str
    passed: bool
    actual_value: Any
    expected_value: Any
    tolerance: Optional[float] = None
    message: str
    error: Optional[str] = None


class TestExecutionResult(BaseModel):
    """Complete test execution result"""
    test_case_id: str
    test_name: str
    result: TestResult
    overall_passed: bool
    
    # Timing information
    execution_start_time: str
    execution_end_time: str
    execution_duration: float  # seconds
    
    # Validation results
    validation_results: List[ValidationResult] = []
    
    # Robot state information
    initial_joint_state: Optional[List[float]] = None
    final_joint_state: Optional[List[float]] = None
    
    # Container information
    container_id: Optional[str] = None
    docker_image: str
    headless_mode: bool
    
    # Logs and artifacts
    stdout: str = ""
    stderr: str = ""
    rosbag_path: Optional[str] = None
    gazebo_recording_path: Optional[str] = None
    
    # Error information
    error_message: Optional[str] = None
    exception_traceback: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_case_id": "TC_001",
                "test_name": "Move to home position",
                "result": "passed",
                "overall_passed": True,
                "execution_duration": 12.5,
                "validation_results": [
                    {
                        "check_name": "position_accuracy",
                        "passed": True,
                        "actual_value": 0.008,
                        "expected_value": 0.01,
                        "message": "Position within tolerance"
                    }
                ]
            }
        }


class BatchTestExecutionRequest(BaseModel):
    """Request for batch robot test execution"""
    process_name: str = Field(..., description="Process name from test generation")
    test_ids: List[str] = Field(..., description="Test case IDs to execute")
    
    # Execution settings
    max_parallel: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum parallel headless containers"
    )
    timeout_per_test: int = Field(
        default=300,
        description="Timeout per test in seconds"
    )
    
    # Visual debugging
    visual_test_id: Optional[str] = Field(
        default=None,
        description="Single test ID to run in Gazebo GUI mode (runs simultaneously)"
    )
    enable_gazebo_recording: bool = Field(
        default=False,
        description="Record Gazebo simulation for visual test"
    )
    
    # Docker settings
    docker_image: str = Field(
        default="stlc-robot-ros2:latest",
        description="Docker image name for robot tests"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "process_name": "Robot Joint Movement Tests",
                "test_ids": ["TC_001", "TC_002", "TC_003"],
                "max_parallel": 5,
                "visual_test_id": "TC_001",
                "enable_gazebo_recording": True
            }
        }


class BatchTestExecutionResponse(BaseModel):
    """Response for batch test execution"""
    session_id: str
    message: str
    total_tests: int
    headless_tests: int
    visual_tests: int
    estimated_duration: float  # seconds
    status: str = "initiated"
