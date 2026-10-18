from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import services.docker_executor as docker_module  # noqa: E402
import services.robot_docker_executor as robot_module  # noqa: E402
from services.ros2_executor import ROS2Executor  # noqa: E402


def test_docker_executor_does_not_connect_during_startup(monkeypatch):
    calls = []

    def unavailable():
        calls.append(True)
        raise RuntimeError("daemon unavailable")

    monkeypatch.setattr(docker_module.docker, "from_env", unavailable)
    executor = docker_module.DockerExecutor()

    assert calls == []
    first = executor.get_availability_status()
    second = executor.get_availability_status()

    assert first["available"] is False
    assert first["optional"] is True
    assert "daemon unavailable" in first["reason"]
    assert second["available"] is False
    assert len(calls) == 1


def test_ros2_status_is_optional_and_throttles_missing_docker(monkeypatch):
    calls = []

    def unavailable():
        calls.append(True)
        raise RuntimeError("named pipe missing")

    monkeypatch.setattr(docker_module.docker, "from_env", unavailable)
    executor = ROS2Executor()

    first = executor.get_status()
    second = executor.get_status()

    assert first["available"] is False
    assert first["optional"] is True
    assert first["backend"] == "docker"
    assert "named pipe missing" in first["reason"]
    assert second["available"] is False
    assert len(calls) == 1


def test_robot_executor_does_not_connect_during_startup(monkeypatch):
    calls = []

    def unavailable():
        calls.append(True)
        raise RuntimeError("daemon unavailable")

    monkeypatch.setattr(robot_module.docker, "from_env", unavailable)
    executor = robot_module.RobotDockerExecutor()

    assert calls == []
    assert executor.is_available is False
    assert executor.is_available is False
    assert len(calls) == 1
