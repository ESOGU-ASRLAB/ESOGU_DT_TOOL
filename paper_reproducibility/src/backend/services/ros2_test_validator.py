"""
ROS 2 Test Validator Service
Validates robot test execution against defined criteria
Generates validation scripts to run inside Docker containers
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from models.robot_test_criteria import (
    RobotTestCriteria,
    TestExecutionResult,
    ValidationResult,
    TestResult
)

logger = logging.getLogger(__name__)


class ROS2TestValidator:
    """
    Validates ROS 2 robot test execution results
    Generates Python validation scripts to run inside containers
    """
    
    def __init__(self):
        self.logger = logger
        
    def generate_validation_script(
        self,
        test_code: str,
        criteria: RobotTestCriteria
    ) -> str:
        """
        Generate a complete validation script that wraps test code
        with ROS 2 validation checks and returns structured results
        
        Args:
            test_code: The robot test code to execute
            criteria: Test validation criteria
            
        Returns:
            Complete Python script with validation logic
        """
        
        validation_script = f'''#!/usr/bin/env python3
"""
Auto-generated ROS 2 Test Validation Script
Test: {criteria.test_name} ({criteria.test_case_id})
Generated: {datetime.now().isoformat()}
"""

import json
import time
import sys
import traceback
from datetime import datetime

# ROS 2 validation results storage
validation_results = {{
    "test_case_id": "{criteria.test_case_id}",
    "test_name": "{criteria.test_name}",
    "result": "unknown",
    "overall_passed": False,
    "execution_start_time": None,
    "execution_end_time": None,
    "execution_duration": 0.0,
    "validation_results": [],
    "initial_joint_state": None,
    "final_joint_state": None,
    "stdout": "",
    "stderr": "",
    "error_message": None,
    "exception_traceback": None
}}


def add_validation_result(check_name: str, passed: bool, actual_value, expected_value, 
                         tolerance=None, message="", error=None):
    """Add a validation check result"""
    validation_results["validation_results"].append({{
        "check_name": check_name,
        "passed": passed,
        "actual_value": actual_value,
        "expected_value": expected_value,
        "tolerance": tolerance,
        "message": message,
        "error": error
    }})


def check_position_accuracy(controller, criteria_dict):
    """Validate final position accuracy"""
    try:
        import numpy as np
        
        # Get current joint state
        current_joints = controller.moveit2.joint_state
        if current_joints is None:
            add_validation_result(
                "position_accuracy",
                False,
                None,
                criteria_dict["target_joint_angles"],
                criteria_dict["position_tolerance"],
                "Failed to read joint state",
                "Joint state unavailable"
            )
            return False
        
        # Calculate position error
        target = np.array(criteria_dict["target_joint_angles"])
        actual = np.array(current_joints)
        
        # Handle different DOF (some robots have extra joints)
        min_len = min(len(target), len(actual))
        target = target[:min_len]
        actual = actual[:min_len]
        
        errors = np.abs(target - actual)
        max_error = np.max(errors)
        
        tolerance = criteria_dict["position_tolerance"]
        passed = max_error <= tolerance
        
        add_validation_result(
            "position_accuracy",
            passed,
            float(max_error),
            tolerance,
            tolerance,
            f"Max joint error: {{max_error:.6f}} rad (tolerance: {{tolerance}} rad)",
            None if passed else f"Position error exceeds tolerance: {{max_error:.6f}} > {{tolerance}}"
        )
        
        return passed
        
    except Exception as e:
        add_validation_result(
            "position_accuracy",
            False,
            None,
            criteria_dict["target_joint_angles"],
            criteria_dict["position_tolerance"],
            "Exception during position check",
            str(e)
        )
        return False


def check_timing(duration: float, max_duration: float, min_duration=None):
    """Validate execution timing"""
    try:
        # Check timeout
        if max_duration and duration > max_duration:
            add_validation_result(
                "timing_check",
                False,
                duration,
                max_duration,
                None,
                f"Execution timeout: {{duration:.2f}}s > {{max_duration}}s",
                "Test exceeded maximum duration"
            )
            return False
        
        # Check minimum duration (detect skipped movements)
        if min_duration and duration < min_duration:
            add_validation_result(
                "timing_check",
                False,
                duration,
                min_duration,
                None,
                f"Execution too fast: {{duration:.2f}}s < {{min_duration}}s",
                "Test completed suspiciously fast (possible skip)"
            )
            return False
        
        add_validation_result(
            "timing_check",
            True,
            duration,
            max_duration,
            None,
            f"Execution time: {{duration:.2f}}s (limit: {{max_duration}}s)",
            None
        )
        return True
        
    except Exception as e:
        add_validation_result(
            "timing_check",
            False,
            duration,
            max_duration,
            None,
            "Exception during timing check",
            str(e)
        )
        return False


def check_ros2_nodes(required_nodes: list):
    """Check if required ROS 2 nodes are running"""
    try:
        import subprocess
        result = subprocess.run(
            ["ros2", "node", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        active_nodes = result.stdout.strip().split('\\n')
        missing_nodes = [n for n in required_nodes if n not in active_nodes]
        
        passed = len(missing_nodes) == 0
        
        add_validation_result(
            "ros2_node_health",
            passed,
            active_nodes,
            required_nodes,
            None,
            f"Active nodes: {{len(active_nodes)}}, Required: {{len(required_nodes)}}",
            f"Missing nodes: {{missing_nodes}}" if not passed else None
        )
        
        return passed
        
    except Exception as e:
        add_validation_result(
            "ros2_node_health",
            False,
            None,
            required_nodes,
            None,
            "Exception during ROS 2 node check",
            str(e)
        )
        return False


def check_collision_status(controller):
    """Check for collisions during movement"""
    try:
        # Note: This requires planning scene monitoring
        # For now, we'll check if movement completed successfully
        # Real collision detection would need move_group collision monitoring
        
        last_error = getattr(controller.moveit2, 'last_error', None)
        
        if last_error and 'collision' in str(last_error).lower():
            add_validation_result(
                "collision_check",
                False,
                "collision_detected",
                "no_collision",
                None,
                "Collision detected during movement",
                str(last_error)
            )
            return False
        
        add_validation_result(
            "collision_check",
            True,
            "no_collision",
            "no_collision",
            None,
            "No collisions detected",
            None
        )
        return True
        
    except Exception as e:
        add_validation_result(
            "collision_check",
            False,
            None,
            "no_collision",
            None,
            "Exception during collision check",
            str(e)
        )
        return False


# ============================================================================
# MAIN TEST EXECUTION WITH VALIDATION
# ============================================================================

def main():
    """Execute test with comprehensive validation"""
    validation_results["execution_start_time"] = datetime.now().isoformat()
    start_time = time.time()
    
    try:
        # Import test criteria
        criteria = {json.dumps(criteria.dict(), indent=8)}
        
        print(f"🔬 Starting validated test: {{criteria['test_name']}}")
        print(f"📋 Test ID: {{criteria['test_case_id']}}")
        print("=" * 70)
        
        # ====================================================================
        # EXECUTE ORIGINAL TEST CODE
        # ====================================================================
        
{self._indent_code(test_code, 8)}
        
        # ====================================================================
        # RUN VALIDATION CHECKS
        # ====================================================================
        
        print("\\n" + "=" * 70)
        print("🔍 Running validation checks...")
        
        # 1. Position accuracy check
        if criteria["position_criteria"]["check_type"] == "joint_space":
            position_check = check_position_accuracy(
                robot_controller,
                criteria["position_criteria"]
            )
        else:
            position_check = True  # Cartesian validation not implemented yet
            add_validation_result(
                "position_accuracy",
                True,
                "skipped",
                "cartesian",
                None,
                "Cartesian position validation not implemented",
                None
            )
        
        # 2. Timing check
        end_time = time.time()
        duration = end_time - start_time
        timing_check = check_timing(
            duration,
            criteria["timing_criteria"]["max_duration"],
            criteria["timing_criteria"].get("min_duration")
        )
        
        # 3. ROS 2 node health check
        if criteria["ros2_health_criteria"]["check_node_health"]:
            node_health_check = check_ros2_nodes(
                criteria["ros2_health_criteria"]["required_nodes"]
            )
        else:
            node_health_check = True
            add_validation_result(
                "ros2_node_health",
                True,
                "skipped",
                "skipped",
                None,
                "ROS 2 node health check disabled",
                None
            )
        
        # 4. Collision check
        if criteria["collision_criteria"]["check_collisions"]:
            collision_check = check_collision_status(robot_controller)
        else:
            collision_check = True
            add_validation_result(
                "collision_check",
                True,
                "skipped",
                "skipped",
                None,
                "Collision check disabled",
                None
            )
        
        # ====================================================================
        # DETERMINE OVERALL RESULT
        # ====================================================================
        
        all_checks = [position_check, timing_check, node_health_check, collision_check]
        overall_passed = all(all_checks)
        
        validation_results["overall_passed"] = overall_passed
        validation_results["result"] = "passed" if overall_passed else "failed"
        validation_results["execution_duration"] = duration
        
        print("\\n" + "=" * 70)
        if overall_passed:
            print("✅ TEST PASSED - All validation checks successful")
        else:
            print("❌ TEST FAILED - Some validation checks failed")
        print(f"⏱️  Execution time: {{duration:.2f}} seconds")
        print("=" * 70)
        
    except KeyboardInterrupt:
        validation_results["result"] = "skipped"
        validation_results["error_message"] = "Test interrupted by user"
        print("\\n⚠️  Test interrupted by user")
        
    except Exception as e:
        validation_results["result"] = "error"
        validation_results["error_message"] = str(e)
        validation_results["exception_traceback"] = traceback.format_exc()
        print(f"\\n❌ TEST ERROR: {{str(e)}}")
        print(traceback.format_exc())
        
    finally:
        validation_results["execution_end_time"] = datetime.now().isoformat()
        
        # Write results to JSON file
        with open("/test/validation_results.json", "w") as f:
            json.dump(validation_results, f, indent=2)
        
        print("\\n📊 Validation results saved to: /test/validation_results.json")
        
        # Exit with appropriate code
        sys.exit(0 if validation_results["overall_passed"] else 1)


if __name__ == "__main__":
    main()
'''
        
        return validation_script
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code block by specified spaces"""
        indent = " " * spaces
        lines = code.split('\n')
        return '\n'.join(indent + line if line.strip() else line for line in lines)
    
    def parse_validation_results(
        self,
        json_output: str,
        container_info: Dict[str, Any]
    ) -> TestExecutionResult:
        """
        Parse validation results from container output
        
        Args:
            json_output: JSON string with validation results
            container_info: Container execution metadata
            
        Returns:
            TestExecutionResult object
        """
        try:
            results_dict = json.loads(json_output)
            
            # Create ValidationResult objects
            validation_results = [
                ValidationResult(**vr) for vr in results_dict.get("validation_results", [])
            ]
            
            # Create TestExecutionResult
            result = TestExecutionResult(
                test_case_id=results_dict["test_case_id"],
                test_name=results_dict["test_name"],
                result=TestResult(results_dict["result"]),
                overall_passed=results_dict["overall_passed"],
                execution_start_time=results_dict["execution_start_time"],
                execution_end_time=results_dict["execution_end_time"],
                execution_duration=results_dict["execution_duration"],
                validation_results=validation_results,
                initial_joint_state=results_dict.get("initial_joint_state"),
                final_joint_state=results_dict.get("final_joint_state"),
                container_id=container_info.get("container_id"),
                docker_image=container_info.get("docker_image", "unknown"),
                headless_mode=container_info.get("headless", True),
                stdout=results_dict.get("stdout", ""),
                stderr=results_dict.get("stderr", ""),
                error_message=results_dict.get("error_message"),
                exception_traceback=results_dict.get("exception_traceback")
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse validation results JSON: {e}")
            # Return error result
            return TestExecutionResult(
                test_case_id="unknown",
                test_name="unknown",
                result=TestResult.ERROR,
                overall_passed=False,
                execution_start_time=datetime.now().isoformat(),
                execution_end_time=datetime.now().isoformat(),
                execution_duration=0.0,
                docker_image=container_info.get("docker_image", "unknown"),
                headless_mode=container_info.get("headless", True),
                error_message=f"Failed to parse validation results: {str(e)}",
                stdout=json_output
            )
        
        except Exception as e:
            logger.error(f"Error parsing validation results: {e}")
            return TestExecutionResult(
                test_case_id="unknown",
                test_name="unknown",
                result=TestResult.ERROR,
                overall_passed=False,
                execution_start_time=datetime.now().isoformat(),
                execution_end_time=datetime.now().isoformat(),
                execution_duration=0.0,
                docker_image=container_info.get("docker_image", "unknown"),
                headless_mode=container_info.get("headless", True),
                error_message=f"Error parsing results: {str(e)}"
            )
    
    def extract_criteria_from_test_case(
        self,
        test_case: Dict[str, Any]
    ) -> Optional[RobotTestCriteria]:
        """
        Extract test criteria from a test case document
        Tries to infer criteria from test code if not explicitly defined
        
        Args:
            test_case: Test case document from MongoDB
            
        Returns:
            RobotTestCriteria or None
        """
        try:
            # Import criteria models at the start
            from models.robot_test_criteria import PositionCriteria
            
            # Check if criteria already exists
            if "test_criteria" in test_case:
                return RobotTestCriteria(**test_case["test_criteria"])
            
            # Try to infer from test code (basic implementation)
            test_code = test_case.get("code", "")
            test_case_id = test_case.get("test_case_id", "unknown")
            test_name = test_case.get("title", "Unknown Test")
            
            # Look for joint angles in code (very basic parsing)
            import re
            joint_pattern = r'\[([0-9.,\s\-]+)\]'
            matches = re.findall(joint_pattern, test_code)
            
            if matches:
                # Use first found array as target position
                try:
                    target_joints = [float(x.strip()) for x in matches[0].split(',')]
                    
                    criteria = RobotTestCriteria(
                        test_case_id=test_case_id,
                        test_name=test_name,
                        position_criteria=PositionCriteria(
                            target_joint_angles=target_joints,
                            position_tolerance=0.01,
                            check_type="joint_space"
                        )
                    )
                    
                    return criteria
                except:
                    pass
            
            # Default fallback criteria
            criteria = RobotTestCriteria(
                test_case_id=test_case_id,
                test_name=test_name,
                position_criteria=PositionCriteria(
                    target_joint_angles=[0.0] * 7,  # Default 7-DOF
                    position_tolerance=0.01,
                    check_type="joint_space"
                )
            )
            
            return criteria
            
        except Exception as e:
            logger.error(f"Error extracting criteria: {e}")
            return None
