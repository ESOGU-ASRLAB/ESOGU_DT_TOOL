"""
remote_execution_service.py
---------------------------
Service for managing remote/local test execution folders for robot scenarios.
This service handles:
1. Creating execution folders (local/network paths)
2. Deploying source files to execution folder
3. Creating metadata for robot consumption
4. Collecting and parsing results from execution folder
"""

import os
import shutil
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import hashlib

logger = logging.getLogger(__name__)


class RemoteExecutionService:
    """
    Manages remote/local execution folders for robot test scenarios.
    Supports both local paths and network shares (UNC paths on Windows).
    """
    
    def __init__(self):
        self.deployment_metadata_file = "deployment_info.json"
        self.results_metadata_file = "execution_results.json"
        self.status_file = "execution_status.json"
    
    def create_execution_folder(
        self, 
        base_path: str, 
        session_id: str,
        folder_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an execution folder at specified path (local or network).
        
        Args:
            base_path: Base directory path (can be UNC path like \\\\server\\share)
            session_id: Session identifier for this execution
            folder_name: Optional custom folder name
            
        Returns:
            Dict with folder_path, created timestamp, and status
        """
        try:
            # Generate folder name if not provided
            if not folder_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                folder_name = f"test_exec_{session_id}_{timestamp}"
            
            # Create full path
            execution_folder = Path(base_path) / folder_name
            
            # Create folder structure
            execution_folder.mkdir(parents=True, exist_ok=True)
            (execution_folder / "source_files").mkdir(exist_ok=True)
            (execution_folder / "results").mkdir(exist_ok=True)
            (execution_folder / "logs").mkdir(exist_ok=True)
            
            # Create initial status file
            status_data = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "status": "ready",
                "deployment_status": "pending",
                "execution_status": "pending",
                "robot_accessed": False,
                "last_modified": datetime.now().isoformat()
            }
            
            status_file_path = execution_folder / self.status_file
            with open(status_file_path, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Created execution folder: {execution_folder}")
            
            return {
                "success": True,
                "folder_path": str(execution_folder),
                "folder_name": folder_name,
                "created_at": status_data["created_at"],
                "status": status_data["status"],
                "subfolders": {
                    "source_files": str(execution_folder / "source_files"),
                    "results": str(execution_folder / "results"),
                    "logs": str(execution_folder / "logs")
                }
            }
            
        except PermissionError as e:
            logger.error(f"❌ Permission denied accessing {base_path}: {e}")
            return {
                "success": False,
                "error": f"Permission denied: {str(e)}",
                "error_type": "permission_error"
            }
        except Exception as e:
            logger.error(f"❌ Error creating execution folder: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "general_error"
            }
    
    def deploy_source_files(
        self,
        execution_folder: str,
        source_files: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deploy source files to execution folder with metadata for robot.
        
        Args:
            execution_folder: Path to execution folder
            source_files: List of dicts with 'filename', 'content' or 'source_path'
            metadata: Additional metadata for robot consumption
            
        Returns:
            Dict with deployment status and file list
        """
        try:
            execution_path = Path(execution_folder)
            source_path = execution_path / "source_files"
            
            if not source_path.exists():
                raise ValueError(f"Source files directory not found: {source_path}")
            
            deployed_files = []
            file_checksums = {}
            
            # Deploy each file
            for file_info in source_files:
                filename = file_info.get('filename')
                if not filename:
                    logger.warning("⚠️ File without filename, skipping")
                    continue
                
                target_path = source_path / filename
                
                # Handle content-based or path-based deployment
                if 'content' in file_info:
                    # Write content directly
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(file_info['content'])
                    content = file_info['content']
                    
                elif 'source_path' in file_info:
                    # Copy from source path
                    src_path = Path(file_info['source_path'])
                    if src_path.exists():
                        shutil.copy2(src_path, target_path)
                        with open(src_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    else:
                        logger.warning(f"⚠️ Source file not found: {src_path}")
                        continue
                else:
                    logger.warning(f"⚠️ File {filename} has no content or source_path")
                    continue
                
                # Calculate checksum
                checksum = hashlib.md5(content.encode('utf-8')).hexdigest()
                file_checksums[filename] = checksum
                
                deployed_files.append({
                    "filename": filename,
                    "path": str(target_path),
                    "size": len(content),
                    "checksum": checksum,
                    "deployed_at": datetime.now().isoformat()
                })
                
                logger.info(f"✅ Deployed file: {filename}")
            
            # Create deployment metadata
            deployment_data = {
                "deployment_id": hashlib.md5(
                    f"{execution_folder}{datetime.now().isoformat()}".encode()
                ).hexdigest()[:12],
                "deployed_at": datetime.now().isoformat(),
                "file_count": len(deployed_files),
                "files": deployed_files,
                "checksums": file_checksums,
                "metadata": metadata or {},
                "robot_instructions": {
                    "source_folder": str(source_path),
                    "results_folder": str(execution_path / "results"),
                    "logs_folder": str(execution_path / "logs"),
                    "status_file": str(execution_path / self.status_file),
                    "instructions": [
                        "1. Read test files from source_folder",
                        "2. Execute tests in your environment",
                        "3. Write results to results_folder in JSON format",
                        "4. Write execution logs to logs_folder",
                        "5. Update status_file with execution_status='completed'"
                    ]
                }
            }
            
            # Write deployment metadata
            metadata_path = execution_path / self.deployment_metadata_file
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(deployment_data, f, indent=2, ensure_ascii=False)
            
            # Update status file
            self._update_status(
                execution_folder,
                deployment_status="completed",
                status="awaiting_execution"
            )
            
            logger.info(f"✅ Deployed {len(deployed_files)} files to {execution_folder}")
            
            return {
                "success": True,
                "deployment_id": deployment_data["deployment_id"],
                "deployed_at": deployment_data["deployed_at"],
                "file_count": len(deployed_files),
                "files": deployed_files,
                "metadata_path": str(metadata_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Error deploying source files: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_execution_status(self, execution_folder: str) -> Dict[str, Any]:
        """
        Check current status of execution folder.
        Monitors if robot has accessed/completed execution.
        
        Args:
            execution_folder: Path to execution folder
            
        Returns:
            Dict with current status information
        """
        try:
            execution_path = Path(execution_folder)
            status_file = execution_path / self.status_file
            
            if not status_file.exists():
                return {
                    "success": False,
                    "error": "Status file not found",
                    "folder_exists": execution_path.exists()
                }
            
            # Read status file
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
            
            # Check for result files
            results_folder = execution_path / "results"
            result_files = list(results_folder.glob("*.json")) if results_folder.exists() else []
            
            # Check for log files
            logs_folder = execution_path / "logs"
            log_files = list(logs_folder.glob("*.log")) if logs_folder.exists() else []
            
            # Detect robot access by checking file modification times
            source_folder = execution_path / "source_files"
            robot_accessed = False
            if source_folder.exists():
                source_files = list(source_folder.iterdir())
                if source_files:
                    # Check if files were accessed after deployment
                    for file in source_files:
                        access_time = datetime.fromtimestamp(file.stat().st_atime)
                        created_time = datetime.fromisoformat(status_data.get("created_at"))
                        if access_time > created_time:
                            robot_accessed = True
                            break
            
            return {
                "success": True,
                "session_id": status_data.get("session_id"),
                "status": status_data.get("status"),
                "deployment_status": status_data.get("deployment_status"),
                "execution_status": status_data.get("execution_status"),
                "robot_accessed": robot_accessed,
                "created_at": status_data.get("created_at"),
                "last_modified": status_data.get("last_modified"),
                "result_files_count": len(result_files),
                "log_files_count": len(log_files),
                "has_results": len(result_files) > 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking execution status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def collect_results(
        self,
        execution_folder: str,
        result_file_pattern: str = "*.json"
    ) -> Dict[str, Any]:
        """
        Collect and parse results from execution folder.
        
        Args:
            execution_folder: Path to execution folder
            result_file_pattern: Glob pattern for result files (default: *.json)
            
        Returns:
            Dict with collected results
        """
        try:
            execution_path = Path(execution_folder)
            results_folder = execution_path / "results"
            
            if not results_folder.exists():
                return {
                    "success": False,
                    "error": "Results folder not found"
                }
            
            # Find result files
            result_files = list(results_folder.glob(result_file_pattern))
            
            if not result_files:
                return {
                    "success": True,
                    "results_available": False,
                    "message": "No result files found yet",
                    "results_folder": str(results_folder)
                }
            
            # Collect results
            collected_results = []
            for result_file in result_files:
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        if result_file.suffix == '.json':
                            result_data = json.load(f)
                        else:
                            result_data = f.read()
                    
                    collected_results.append({
                        "filename": result_file.name,
                        "path": str(result_file),
                        "size": result_file.stat().st_size,
                        "modified_at": datetime.fromtimestamp(
                            result_file.stat().st_mtime
                        ).isoformat(),
                        "data": result_data
                    })
                except Exception as e:
                    logger.error(f"❌ Error reading result file {result_file}: {e}")
                    collected_results.append({
                        "filename": result_file.name,
                        "error": str(e)
                    })
            
            # Update status
            self._update_status(
                execution_folder,
                status="results_collected",
                execution_status="completed"
            )
            
            # Parse and aggregate results
            aggregated_results = self._aggregate_results(collected_results)
            
            logger.info(f"✅ Collected {len(collected_results)} result files")
            
            return {
                "success": True,
                "results_available": True,
                "collected_at": datetime.now().isoformat(),
                "result_count": len(collected_results),
                "results": collected_results,
                "aggregated": aggregated_results
            }
            
        except Exception as e:
            logger.error(f"❌ Error collecting results: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _update_status(
        self,
        execution_folder: str,
        **status_updates
    ) -> bool:
        """
        Update status file with new information.
        
        Args:
            execution_folder: Path to execution folder
            **status_updates: Key-value pairs to update in status
            
        Returns:
            Success status
        """
        try:
            execution_path = Path(execution_folder)
            status_file = execution_path / self.status_file
            
            if status_file.exists():
                with open(status_file, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
            else:
                status_data = {}
            
            # Update with new values
            status_data.update(status_updates)
            status_data["last_modified"] = datetime.now().isoformat()
            
            # Write back
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating status: {e}")
            return False
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate multiple result files into summary statistics.
        
        Args:
            results: List of result file data
            
        Returns:
            Aggregated statistics
        """
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        execution_time = 0.0
        
        for result in results:
            if 'error' in result:
                continue
            
            data = result.get('data', {})
            if isinstance(data, dict):
                # Try to extract common test result fields
                total_tests += data.get('total_tests', 0)
                passed_tests += data.get('passed', 0)
                failed_tests += data.get('failed', 0)
                skipped_tests += data.get('skipped', 0)
                execution_time += data.get('execution_time', 0.0)
        
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "pass_rate": round(pass_rate, 2),
            "total_execution_time": round(execution_time, 2),
            "summary": f"{passed_tests}/{total_tests} tests passed ({pass_rate:.1f}%)"
        }
    
    def list_execution_folders(self, base_path: str) -> Dict[str, Any]:
        """
        List all execution folders in a base directory.
        
        Args:
            base_path: Base directory to scan
            
        Returns:
            List of execution folders with their status
        """
        try:
            base_dir = Path(base_path)
            
            if not base_dir.exists():
                return {
                    "success": False,
                    "error": "Base path does not exist"
                }
            
            execution_folders = []
            
            # Scan for folders with status files
            for item in base_dir.iterdir():
                if item.is_dir():
                    status_file = item / self.status_file
                    if status_file.exists():
                        status = self.check_execution_status(str(item))
                        if status.get('success'):
                            execution_folders.append({
                                "folder_name": item.name,
                                "folder_path": str(item),
                                **status
                            })
            
            return {
                "success": True,
                "base_path": str(base_dir),
                "folder_count": len(execution_folders),
                "folders": execution_folders
            }
            
        except Exception as e:
            logger.error(f"❌ Error listing execution folders: {e}")
            return {
                "success": False,
                "error": str(e)
            }
