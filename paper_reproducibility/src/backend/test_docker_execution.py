"""
Test script to demonstrate Docker-based robot arm simulation
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_docker_status():
    """Check if Docker is available"""
    print("🔍 Checking Docker status...")
    response = requests.get(f"{BASE_URL}/api/docker-execution/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Docker available: {data['docker_available']}")
        print(f"   Images: {len(data['images'])} available")
        print(f"   Containers: {data['container_status']}")
    else:
        print(f"❌ Failed to get Docker status: {response.status_code}")
    
    print()

def test_robot_simulation():
    """Run robot arm simulation test"""
    print("🤖 Running robot arm simulation test...")
    
    robot_test_code = """
# Test robot movements
print("Starting robot test sequence...")

# Test 1: Move to home position
success, pos = robot.move_to_position([0, 0, 0])
print(f"Home position: {pos}")

# Test 2: Move to working position
success, pos = robot.move_to_position([0.5, 0.3, 0.2])
print(f"Working position 1: {pos}")

# Test 3: Move to another position
success, pos = robot.move_to_position([0.8, 0.4, 0.3])
print(f"Working position 2: {pos}")

# Test 4: Return to home
success, pos = robot.move_to_position([0, 0, 0])
print(f"Returned to home: {pos}")

print("\\n✅ Robot test completed successfully!")
"""
    
    payload = {
        "test_code": robot_test_code,
        "robot_type": "industrial",  # Try industrial 6-DOF robot
        "simulation_config": {
            "precision": "high",
            "simulation_speed": 1.0
        }
    }
    
    print(f"📤 Sending request to execute robot simulation...")
    response = requests.post(
        f"{BASE_URL}/api/docker-execution/execute-robot-simulation",
        json=payload,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n{'='*60}")
        print("SIMULATION RESULTS")
        print(f"{'='*60}")
        print(f"Success: {result['success']}")
        print(f"Exit Code: {result.get('exit_code', 'N/A')}")
        print(f"\nOutput:")
        print(result['output'])
        print(f"{'='*60}\n")
    else:
        print(f"❌ Simulation failed: {response.status_code}")
        print(response.text)
    
    print()

def test_simple_python_execution():
    """Test simple Python code execution in Docker"""
    print("🐍 Testing simple Python code execution...")
    
    test_code = """
import sys
print(f"Python version: {sys.version}")
print("\\nRunning tests...")

# Simple test cases
def test_math():
    assert 2 + 2 == 4
    print("✅ Math test passed")

def test_strings():
    assert "hello".upper() == "HELLO"
    print("✅ String test passed")

def test_lists():
    lst = [1, 2, 3]
    assert len(lst) == 3
    print("✅ List test passed")

# Run tests
test_math()
test_strings()
test_lists()

print("\\n✅ All tests completed successfully!")
"""
    
    payload = {
        "test_code": test_code,
        "language": "python",
        "timeout": 60
    }
    
    print(f"📤 Sending request to execute Python code...")
    response = requests.post(
        f"{BASE_URL}/api/docker-execution/execute",
        json=payload,
        timeout=90
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n{'='*60}")
        print("EXECUTION RESULTS")
        print(f"{'='*60}")
        print(f"Success: {result['success']}")
        print(f"Exit Code: {result.get('exit_code', 'N/A')}")
        print(f"\nOutput:")
        print(result['output'])
        print(f"{'='*60}\n")
    else:
        print(f"❌ Execution failed: {response.status_code}")
        print(response.text)
    
    print()

def test_with_custom_packages():
    """Test execution with custom Python packages"""
    print("📦 Testing execution with custom packages...")
    
    test_code = """
import numpy as np
import pandas as pd

print("Testing NumPy...")
arr = np.array([1, 2, 3, 4, 5])
print(f"Array: {arr}")
print(f"Mean: {np.mean(arr)}")
print(f"Sum: {np.sum(arr)}")

print("\\nTesting Pandas...")
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6]
})
print(df)

print("\\n✅ Package test completed!")
"""
    
    payload = {
        "test_code": test_code,
        "language": "python",
        "additional_packages": ["numpy", "pandas"],
        "timeout": 120
    }
    
    print(f"📤 Sending request with custom packages (numpy, pandas)...")
    response = requests.post(
        f"{BASE_URL}/api/docker-execution/execute",
        json=payload,
        timeout=150
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n{'='*60}")
        print("EXECUTION RESULTS")
        print(f"{'='*60}")
        print(f"Success: {result['success']}")
        print(f"Exit Code: {result.get('exit_code', 'N/A')}")
        print(f"\nOutput:")
        print(result['output'])
        print(f"{'='*60}\n")
    else:
        print(f"❌ Execution failed: {response.status_code}")
        print(response.text)
    
    print()

def get_available_robots():
    """Get list of available robot types"""
    print("🤖 Fetching available robot types...")
    response = requests.get(f"{BASE_URL}/api/docker-execution/available-robots")
    
    if response.status_code == 200:
        data = response.json()
        print("Available robot types:")
        for robot in data['robot_types']:
            print(f"  • {robot['name']} ({robot['id']})")
            print(f"    DOF: {robot['dof']}, {robot['description']}")
    else:
        print(f"❌ Failed to fetch robot types: {response.status_code}")
    
    print()

def main():
    """Run all tests"""
    print("="*60)
    print("DOCKER-BASED TEST EXECUTION - DEMO")
    print("="*60)
    print()
    
    try:
        # Test 1: Check Docker status
        test_docker_status()
        
        # Test 2: Get available robot types
        get_available_robots()
        
        # Test 3: Simple Python execution
        test_simple_python_execution()
        
        # Test 4: Execution with custom packages
        test_with_custom_packages()
        
        # Test 5: Robot arm simulation
        test_robot_simulation()
        
        print("="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server.")
        print("Please ensure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    main()
