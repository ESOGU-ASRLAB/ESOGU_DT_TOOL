"""
docker_executor.py
------------------
Docker-based test execution service for isolated test environments
Supports running tests in containerized environments including hardware simulators
"""

import logging
import os
import tempfile
import shutil
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import asyncio
import time

try:
    import docker
except ImportError:  # Optional dependency: core STLC flows do not require Docker.
    docker = None

logger = logging.getLogger(__name__)

class DockerExecutor:
    """Service for executing tests in Docker containers"""
    
    def __init__(self):
        # Docker is an optional execution backend. Do not contact the daemon
        # during application startup; connect only when a Docker operation is
        # explicitly requested.
        self.client = None
        self._last_connection_attempt = 0.0
        self._retry_interval_seconds = 30.0
        self._unavailable_reason = "Docker execution is optional and not currently available."

    def _get_client(self):
        if self.client is not None:
            return self.client
        now = time.monotonic()
        if now - self._last_connection_attempt < self._retry_interval_seconds:
            return None
        self._last_connection_attempt = now
        if docker is None:
            self._unavailable_reason = "docker-py is not installed; Docker execution remains disabled."
            return None
        try:
            self.client = docker.from_env()
            self.client.ping()
            self._unavailable_reason = ""
            logger.info("Docker optional execution backend is available")
        except Exception as e:
            self.client = None
            self._unavailable_reason = str(e)
            logger.info("Docker optional execution backend is unavailable")
        return self.client
    
    def is_available(self) -> bool:
        """Check if Docker is available and running"""
        client = self._get_client()
        if client is None:
            return False
        try:
            client.ping()
            return True
        except Exception as e:
            self.client = None
            self._unavailable_reason = str(e)
            logger.info("Docker optional execution backend became unavailable")
            return False

    def get_availability_status(self) -> Dict[str, Any]:
        available = self.is_available()
        return {
            "available": available,
            "optional": True,
            "reason": None if available else self._unavailable_reason,
        }
    
    async def execute_test_in_container(
        self,
        test_code: str,
        language: str = "python",
        base_image: Optional[str] = None,
        additional_packages: Optional[List[str]] = None,
        environment_vars: Optional[Dict[str, str]] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute test code in a Docker container
        
        Args:
            test_code: The test code to execute
            language: Programming language (python, java, javascript, etc.)
            base_image: Custom base Docker image (optional)
            additional_packages: Extra packages to install
            environment_vars: Environment variables for the container
            timeout: Execution timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Docker is not available. Please ensure Docker is installed and running.",
                "output": ""
            }
        
        container = None
        temp_dir = None
        custom_image = None  # Track custom built image for cleanup
        
        try:
            # Create temporary directory for test files
            temp_dir = tempfile.mkdtemp(prefix="stlc_test_")
            
            # Determine file extension and image
            file_ext, docker_image = self._get_language_config(language, base_image)
            
            # Write test code to file
            test_file = os.path.join(temp_dir, f"test_code{file_ext}")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            # Create Dockerfile if additional packages needed
            if additional_packages:
                dockerfile_path = os.path.join(temp_dir, "Dockerfile")
                dockerfile_content = self._generate_dockerfile(
                    docker_image, language, additional_packages
                )
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                
                # Build custom image
                logger.info(f"🔨 Building custom Docker image...")
                image, build_logs = self.client.images.build(
                    path=temp_dir,
                    rm=True,
                    forcerm=True
                )
                custom_image = image  # Save reference for cleanup
                docker_image = image.id
            
            # Prepare command based on language
            command = self._get_execution_command(language, f"test_code{file_ext}")
            
            # Prepare environment variables
            env = environment_vars or {}
            
            # Create and run container
            logger.info(f"🚀 Starting container with image: {docker_image}")
            container = self.client.containers.run(
                image=docker_image,
                command=command,
                volumes={temp_dir: {'bind': '/test', 'mode': 'rw'}},
                working_dir='/test',
                environment=env,
                detach=True,
                remove=False,
                network_mode='bridge',
                mem_limit='512m',
                cpu_quota=100000  # Limit CPU usage
            )
            
            # Wait for container to finish with timeout
            result = container.wait(timeout=timeout)
            exit_code = result.get('StatusCode', -1)
            
            # Get logs
            output = container.logs(stdout=True, stderr=True).decode('utf-8')
            
            # Clean up container
            container.remove(force=True)
            
            success = exit_code == 0
            
            logger.info(f"{'✅' if success else '❌'} Container execution completed with exit code: {exit_code}")
            
            return {
                "success": success,
                "output": output,
                "exit_code": exit_code,
                "error": None if success else f"Exit code: {exit_code}",
                "execution_time": datetime.now().isoformat(),
                "container_info": {
                    "image": docker_image,
                    "language": language
                }
            }
            
        except docker.errors.ContainerError as e:
            logger.error(f"Container error: {str(e)}")
            return {
                "success": False,
                "output": str(e),
                "error": f"Container error: {str(e)}",
                "exit_code": -1
            }
            
        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            return {
                "success": False,
                "output": "",
                "error": f"Execution failed: {str(e)}",
                "exit_code": -1
            }
            
        finally:
            # Clean up container
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
            
            # Clean up custom built image
            if custom_image:
                try:
                    logger.info(f"🧹 Cleaning up custom Docker image: {custom_image.short_id}")
                    self.client.images.remove(image=custom_image.id, force=True)
                    logger.info(f"✅ Custom image removed successfully")
                except Exception as e:
                    logger.warning(f"Failed to remove custom image: {e}")
            
            # Clean up temp directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory: {e}")
    
    async def execute_robot_arm_simulation(
        self,
        test_code: str,
        robot_type: str = "generic",
        simulation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute robot arm simulation tests
        
        Args:
            test_code: Test code for robot control
            robot_type: Type of robot (generic, industrial, collaborative)
            simulation_config: Simulation parameters
            
        Returns:
            Simulation results with trajectory data
        """
        logger.info(f"🤖 Starting robot arm simulation: {robot_type}")
        
        # Use specialized robot simulation image
        base_image = "python:3.9-slim"
        
        # Robot simulation packages
        packages = [
            "numpy",
            "scipy",
            "matplotlib",
            "roboticstoolbox-python",
            "spatialmath-python"
        ]
        
        # Add simulation environment variables
        env_vars = {
            "ROBOT_TYPE": robot_type,
            "SIMULATION_MODE": "true",
            "CONFIG": json.dumps(simulation_config or {})
        }
        
        # Wrap test code with simulation framework
        wrapped_code = self._wrap_robot_simulation_code(test_code, robot_type)
        
        return await self.execute_test_in_container(
            test_code=wrapped_code,
            language="python",
            base_image=base_image,
            additional_packages=packages,
            environment_vars=env_vars,
            timeout=600  # 10 minutes for simulation
        )
    
    def _get_language_config(self, language: str, base_image: Optional[str]) -> tuple:
        """Get file extension and Docker image for language"""
        configs = {
            "python": (".py", base_image or "python:3.9-slim"),
            "javascript": (".js", base_image or "node:18-alpine"),
            "java": (".java", base_image or "openjdk:11-jre-slim"),
            "csharp": (".cs", base_image or "mcr.microsoft.com/dotnet/sdk:6.0"),
            "go": (".go", base_image or "golang:1.19-alpine"),
            "rust": (".rs", base_image or "rust:1.70-slim")
        }
        
        return configs.get(language.lower(), (".py", "python:3.9-slim"))
    
    def _get_execution_command(self, language: str, filename: str) -> str:
        """Get execution command for language"""
        commands = {
            "python": f"python {filename}",
            "javascript": f"node {filename}",
            "java": f"javac {filename} && java {filename.replace('.java', '')}",
            "csharp": f"dotnet run {filename}",
            "go": f"go run {filename}",
            "rust": f"rustc {filename} && ./{filename.replace('.rs', '')}"
        }
        
        return commands.get(language.lower(), f"python {filename}")
    
    def _generate_dockerfile(
        self,
        base_image: str,
        language: str,
        packages: List[str]
    ) -> str:
        """Generate Dockerfile with required packages"""
        if language.lower() == "python":
            packages_str = " ".join(packages)
            return f"""FROM {base_image}
WORKDIR /test
RUN pip install --no-cache-dir {packages_str}
CMD ["python"]
"""
        elif language.lower() == "javascript":
            packages_str = " ".join(packages)
            return f"""FROM {base_image}
WORKDIR /test
RUN npm install -g {packages_str}
CMD ["node"]
"""
        else:
            return f"""FROM {base_image}
WORKDIR /test
CMD ["sh"]
"""
    
    def _wrap_robot_simulation_code(self, test_code: str, robot_type: str) -> str:
        """Wrap test code with robot simulation framework"""
        wrapper = f"""
import os
import json
import numpy as np
from roboticstoolbox import DHRobot, RevoluteDH
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Robot simulation framework
class RobotArmSimulator:
    def __init__(self, robot_type="{robot_type}"):
        self.robot_type = robot_type
        self.robot = self._create_robot()
        self.trajectory = []
        
    def _create_robot(self):
        '''Create robot model based on type'''
        if self.robot_type == "industrial":
            # 6-DOF industrial robot
            links = [
                RevoluteDH(d=0.5, a=0, alpha=np.pi/2),
                RevoluteDH(d=0, a=0.5, alpha=0),
                RevoluteDH(d=0, a=0.4, alpha=0),
                RevoluteDH(d=0.5, a=0, alpha=np.pi/2),
                RevoluteDH(d=0, a=0, alpha=-np.pi/2),
                RevoluteDH(d=0.2, a=0, alpha=0)
            ]
        else:
            # Generic 3-DOF robot
            links = [
                RevoluteDH(d=0.3, a=0, alpha=np.pi/2),
                RevoluteDH(d=0, a=0.4, alpha=0),
                RevoluteDH(d=0, a=0.3, alpha=0)
            ]
        
        return DHRobot(links, name=self.robot_type)
    
    def move_to_position(self, joint_angles):
        '''Move robot to specified joint angles'''
        try:
            T = self.robot.fkine(joint_angles)
            self.trajectory.append({{
                'joint_angles': list(joint_angles),
                'end_effector_position': T.t.tolist(),
                'timestamp': len(self.trajectory)
            }})
            return True, T.t
        except Exception as e:
            return False, str(e)
    
    def get_current_position(self):
        '''Get current end effector position'''
        if self.trajectory:
            return self.trajectory[-1]['end_effector_position']
        return [0, 0, 0]
    
    def get_trajectory_summary(self):
        '''Get trajectory summary'''
        return {{
            'total_moves': len(self.trajectory),
            'positions': [t['end_effector_position'] for t in self.trajectory],
            'joint_angles': [t['joint_angles'] for t in self.trajectory]
        }}

# Initialize simulator
robot = RobotArmSimulator()

# User test code starts here
{test_code}

# Output results
print("\\n" + "="*50)
print("ROBOT ARM SIMULATION RESULTS")
print("="*50)
summary = robot.get_trajectory_summary()
print(f"Total Moves: {{summary['total_moves']}}")
print(f"Final Position: {{summary['positions'][-1] if summary['positions'] else 'N/A'}}")
print("="*50)
"""
        return wrapper
    
    def list_available_images(self) -> List[str]:
        """List available Docker images"""
        if not self.is_available():
            return []
        
        try:
            images = self.client.images.list()
            return [
                img.tags[0] if img.tags else img.short_id
                for img in images
            ]
        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            return []
    
    def pull_image(self, image_name: str) -> bool:
        """Pull a Docker image"""
        if not self.is_available():
            return False
        
        try:
            logger.info(f"📥 Pulling Docker image: {image_name}")
            self.client.images.pull(image_name)
            logger.info(f"✅ Successfully pulled {image_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull image {image_name}: {e}")
            return False
    
    def get_container_status(self) -> Dict[str, Any]:
        """Get status of all STLC containers"""
        if not self.is_available():
            return {"available": False, "containers": []}
        
        try:
            containers = self.client.containers.list(all=True)
            stlc_containers = [
                {
                    "id": c.short_id,
                    "name": c.name,
                    "status": c.status,
                    "image": c.image.tags[0] if c.image.tags else c.image.short_id
                }
                for c in containers
                if "stlc" in c.name.lower()
            ]
            
            return {
                "available": True,
                "total_containers": len(containers),
                "stlc_containers": stlc_containers
            }
        except Exception as e:
            logger.error(f"Failed to get container status: {e}")
            return {"available": False, "error": str(e)}

# Global instance
docker_executor = DockerExecutor()
