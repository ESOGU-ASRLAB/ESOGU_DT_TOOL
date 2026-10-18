"""
Docker Template Files for Test Execution
"""

# Python Test Environment Dockerfile
PYTHON_TEST_DOCKERFILE = """
FROM python:3.9-slim

WORKDIR /test

# Install common testing packages
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    unittest-xml-reporting \
    nose2 \
    behave

# Install additional packages if needed
ARG ADDITIONAL_PACKAGES=""
RUN if [ -n "$ADDITIONAL_PACKAGES" ]; then \
    pip install --no-cache-dir $ADDITIONAL_PACKAGES; \
    fi

COPY . /test

CMD ["pytest", "-v"]
"""

# Robot Simulation Dockerfile
ROBOT_SIMULATION_DOCKERFILE = """
FROM python:3.9-slim

WORKDIR /test

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install robotics packages
RUN pip install --no-cache-dir \
    numpy \
    scipy \
    matplotlib \
    roboticstoolbox-python \
    spatialmath-python \
    sympy

# Copy test files
COPY . /test

CMD ["python", "robot_test.py"]
"""

# Java Test Environment Dockerfile
JAVA_TEST_DOCKERFILE = """
FROM openjdk:11-jdk-slim

WORKDIR /test

# Install Maven for dependency management
RUN apt-get update && apt-get install -y maven && rm -rf /var/lib/apt/lists/*

# Copy test files
COPY . /test

# Compile and run
CMD ["sh", "-c", "javac *.java && java MainTest"]
"""

# JavaScript Test Environment Dockerfile
JAVASCRIPT_TEST_DOCKERFILE = """
FROM node:18-alpine

WORKDIR /test

# Install common testing frameworks
RUN npm install -g \
    jest \
    mocha \
    chai \
    jasmine

# Copy test files
COPY . /test

# Install package dependencies if package.json exists
RUN if [ -f "package.json" ]; then npm install; fi

CMD ["npm", "test"]
"""

# Docker Compose for Complex Test Environments
DOCKER_COMPOSE_TEMPLATE = """
version: '3.8'

services:
  test-runner:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./test_results:/test_results
    environment:
      - TEST_ENV=docker
      - LOG_LEVEL=INFO
    networks:
      - test-network
    depends_on:
      - test-database
      - mock-api

  test-database:
    image: postgres:13-alpine
    environment:
      - POSTGRES_DB=test_db
      - POSTGRES_USER=test_user
      - POSTGRES_PASSWORD=test_password
    networks:
      - test-network
    tmpfs:
      - /var/lib/postgresql/data

  mock-api:
    image: mockserver/mockserver:latest
    environment:
      - MOCKSERVER_PROPERTY_FILE=/config/mockserver.properties
    networks:
      - test-network
    ports:
      - "1080:1080"

networks:
  test-network:
    driver: bridge
"""

# Robot Arm Test Example Code
ROBOT_ARM_TEST_EXAMPLE = """
#!/usr/bin/env python3
'''
Robot Arm Test Example
Test robotic arm movements and control logic
'''

import numpy as np

# Robot instance is automatically available from the simulation framework
print("🤖 Starting Robot Arm Test")
print("=" * 50)

# Test 1: Basic Movement
print("\\nTest 1: Moving to home position")
home_position = [0, 0, 0]
success, position = robot.move_to_position(home_position)
print(f"  Result: {'✅ Success' if success else '❌ Failed'}")
print(f"  Position: {position}")

# Test 2: Workspace Reachability
print("\\nTest 2: Testing workspace boundaries")
test_positions = [
    [0.5, 0.3, 0.2],
    [1.0, 0.5, 0.1],
    [0.8, -0.3, 0.4]
]

reachable_count = 0
for i, pos in enumerate(test_positions, 1):
    success, end_pos = robot.move_to_position(pos)
    if success:
        reachable_count += 1
        print(f"  Position {i}: ✅ Reachable - {end_pos}")
    else:
        print(f"  Position {i}: ❌ Not reachable - {end_pos}")

print(f"\\n  Reachability: {reachable_count}/{len(test_positions)} positions")

# Test 3: Trajectory Following
print("\\nTest 3: Following a circular trajectory")
circle_points = []
for angle in np.linspace(0, 2*np.pi, 8):
    x = 0.5 + 0.2 * np.cos(angle)
    y = 0.2 * np.sin(angle)
    z = 0.3
    circle_points.append([x, y, z])

trajectory_success = True
for i, point in enumerate(circle_points):
    success, pos = robot.move_to_position(point)
    if not success:
        trajectory_success = False
        print(f"  Point {i+1}: ❌ Failed")
        break
    print(f"  Point {i+1}: ✅ Success")

print(f"\\n  Trajectory: {'✅ Completed' if trajectory_success else '❌ Failed'}")

# Test 4: Speed Test
print("\\nTest 4: Rapid movements test")
import time
start_time = time.time()

for _ in range(5):
    robot.move_to_position([0.5, 0.5, 0.2])
    robot.move_to_position([0.5, -0.5, 0.2])

elapsed_time = time.time() - start_time
print(f"  10 movements completed in {elapsed_time:.2f} seconds")
print(f"  Average time per movement: {elapsed_time/10:.3f} seconds")

# Get summary
print("\\n" + "=" * 50)
summary = robot.get_trajectory_summary()
print(f"Total test movements: {summary['total_moves']}")
print(f"Final position: {summary['positions'][-1] if summary['positions'] else 'N/A'}")
print("=" * 50)
print("\\n✅ Robot Arm Test Completed!")
"""

# Simple Python Test Example
SIMPLE_PYTHON_TEST = """
#!/usr/bin/env python3
'''
Simple Python Test Example
'''

def test_addition():
    assert 1 + 1 == 2, "Basic addition failed"
    print("✅ Test 1: Addition passed")

def test_multiplication():
    assert 2 * 3 == 6, "Basic multiplication failed"
    print("✅ Test 2: Multiplication passed")

def test_string_operations():
    assert "hello".upper() == "HELLO", "String upper case failed"
    print("✅ Test 3: String operations passed")

if __name__ == "__main__":
    print("🧪 Running Simple Tests")
    print("=" * 50)
    
    try:
        test_addition()
        test_multiplication()
        test_string_operations()
        print("=" * 50)
        print("\\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\\n❌ Unexpected error: {e}")
"""

# Dockerfile Generator Function
def generate_dockerfile(language: str, packages: list = None) -> str:
    """Generate appropriate Dockerfile based on language and requirements"""
    
    templates = {
        "python": PYTHON_TEST_DOCKERFILE,
        "java": JAVA_TEST_DOCKERFILE,
        "javascript": JAVASCRIPT_TEST_DOCKERFILE,
        "robot_simulation": ROBOT_SIMULATION_DOCKERFILE
    }
    
    template = templates.get(language.lower(), PYTHON_TEST_DOCKERFILE)
    
    if packages:
        # Add packages to the template
        packages_str = " ".join(packages)
        template = template.replace(
            'ARG ADDITIONAL_PACKAGES=""',
            f'ARG ADDITIONAL_PACKAGES="{packages_str}"'
        )
    
    return template

# Export all templates
__all__ = [
    'PYTHON_TEST_DOCKERFILE',
    'ROBOT_SIMULATION_DOCKERFILE',
    'JAVA_TEST_DOCKERFILE',
    'JAVASCRIPT_TEST_DOCKERFILE',
    'DOCKER_COMPOSE_TEMPLATE',
    'ROBOT_ARM_TEST_EXAMPLE',
    'SIMPLE_PYTHON_TEST',
    'generate_dockerfile'
]
