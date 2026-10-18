"""
parallel_docker_executor.py
----------------------------
Parallel Docker test execution service with job queue management
Executes multiple test cases simultaneously in isolated Docker containers
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from services.docker_executor import docker_executor
from core.database import get_database

logger = logging.getLogger(__name__)

class ExecutionStatus(str, Enum):
    """Test execution status states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TestExecutionJob:
    """Represents a single test execution job"""
    
    def __init__(
        self,
        job_id: str,
        test_id: str,
        test_code: str,
        test_name: str,
        source_code: Optional[str] = None
    ):
        self.job_id = job_id
        self.test_id = test_id
        self.test_code = test_code
        self.test_name = test_name
        self.source_code = source_code
        self.status = ExecutionStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.container_id = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary format"""
        return {
            "job_id": self.job_id,
            "test_id": self.test_id,
            "test_name": self.test_name,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": (self.end_time - self.start_time).total_seconds() if (self.start_time and self.end_time) else None,
            "container_id": self.container_id
        }

class BatchExecutionSession:
    """Manages a batch of parallel test executions"""
    
    def __init__(
        self,
        session_id: str,
        process_name: str,
        language: str = "python",
        max_parallel: int = 5,
        timeout: int = 300,
        additional_packages: Optional[List[str]] = None
    ):
        self.session_id = session_id
        self.process_name = process_name
        self.language = language
        self.max_parallel = max_parallel
        self.timeout = timeout
        self.additional_packages = additional_packages
        
        self.jobs: List[TestExecutionJob] = []
        self.status = ExecutionStatus.PENDING
        self.start_time = None
        self.end_time = None
        
        # Statistics
        self.total_tests = 0
        self.completed = 0
        self.failed = 0
        self.running = 0
        self.pending = 0
        
    def add_job(self, job: TestExecutionJob):
        """Add a test execution job to the batch"""
        self.jobs.append(job)
        self.total_tests += 1
        self.pending += 1
    
    def update_statistics(self):
        """Update execution statistics"""
        self.pending = sum(1 for j in self.jobs if j.status == ExecutionStatus.PENDING)
        self.running = sum(1 for j in self.jobs if j.status == ExecutionStatus.RUNNING)
        self.completed = sum(1 for j in self.jobs if j.status == ExecutionStatus.COMPLETED)
        self.failed = sum(1 for j in self.jobs if j.status == ExecutionStatus.FAILED)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current execution progress"""
        self.update_statistics()
        
        success_rate = 0.0
        if self.completed + self.failed > 0:
            success_rate = (self.completed / (self.completed + self.failed)) * 100
        
        return {
            "session_id": self.session_id,
            "process_name": self.process_name,
            "status": self.status.value,
            "total_tests": self.total_tests,
            "pending": self.pending,
            "running": self.running,
            "completed": self.completed,
            "failed": self.failed,
            "success_rate": round(success_rate, 1),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "elapsed_time": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }
    
    def get_results(self) -> Dict[str, Any]:
        """Get detailed execution results"""
        self.update_statistics()
        
        return {
            "session_id": self.session_id,
            "process_name": self.process_name,
            "status": self.status.value,
            "statistics": {
                "total_tests": self.total_tests,
                "completed": self.completed,
                "failed": self.failed,
                "success_rate": round((self.completed / self.total_tests * 100) if self.total_tests > 0 else 0, 1)
            },
            "execution_time": {
                "start": self.start_time.isoformat() if self.start_time else None,
                "end": self.end_time.isoformat() if self.end_time else None,
                "total_seconds": (self.end_time - self.start_time).total_seconds() if (self.start_time and self.end_time) else None
            },
            "jobs": [job.to_dict() for job in self.jobs]
        }

class ParallelDockerExecutor:
    """Service for executing tests in parallel Docker containers"""
    
    def __init__(self):
        self.active_sessions: Dict[str, BatchExecutionSession] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)  # Thread pool for async execution
        logger.info("✅ ParallelDockerExecutor initialized")
    
    async def create_batch_session(
        self,
        process_name: str,
        test_ids: List[str],
        language: str = "python",
        max_parallel: int = 5,
        timeout: int = 300,
        additional_packages: Optional[List[str]] = None
    ) -> str:
        """
        Create a new batch execution session
        
        Args:
            process_name: Test Code Generation process name
            test_ids: List of test IDs to execute
            language: Programming language
            max_parallel: Maximum number of parallel containers
            timeout: Execution timeout per test
            additional_packages: Extra packages to install
            
        Returns:
            Session ID
        """
        session_id = f"batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # Create session
        session = BatchExecutionSession(
            session_id=session_id,
            process_name=process_name,
            language=language,
            max_parallel=max_parallel,
            timeout=timeout,
            additional_packages=additional_packages
        )
        
        # Fetch test data from database
        try:
            db = await get_database()
            collection = db["session_history"]
            
            # Find sessions with test code generation for this process
            query = {"processes.test_code_generation.process_name": process_name}
            logger.info(f"🔍 Searching MongoDB with query: {query}")
            
            cursor = collection.find(query)
            
            test_map = {}
            doc_count = 0
            async for doc in cursor:
                doc_count += 1
                logger.info(f"📄 Found document {doc_count} with session_id: {doc.get('session_id')}")
                
                tcg = doc.get("processes", {}).get("test_code_generation", {})
                output = tcg.get("output", {})
                
                if "generated_tests" in output:
                    tests = output["generated_tests"]
                    logger.info(f"   Found {len(tests)} tests in document")
                    
                    for test in tests:
                        # Try both test_id and test_case_id for compatibility
                        test_id = test.get("test_id") or test.get("test_case_id")
                        logger.info(f"   - Test ID: {test_id}, Looking for: {test_id in test_ids}")
                        
                        if test_id in test_ids:
                            test_map[test_id] = {
                                "test_code": test.get("test_code") or test.get("code", ""),
                                "test_name": test.get("test_name") or test.get("filename", f"Test {test_id}"),
                                "source_code": test.get("source_code", "")
                            }
                            logger.info(f"   ✅ Matched test_id: {test_id}")
            
            logger.info(f"📊 Total documents found: {doc_count}")
            logger.info(f"📊 Total tests mapped: {len(test_map)} out of {len(test_ids)} requested")
            logger.info(f"📋 Requested test_ids: {test_ids}")
            logger.info(f"📋 Mapped test_ids: {list(test_map.keys())}")
            
            # Create jobs
            for test_id in test_ids:
                if test_id in test_map:
                    test_data = test_map[test_id]
                    job = TestExecutionJob(
                        job_id=f"job-{uuid.uuid4().hex[:8]}",
                        test_id=test_id,
                        test_code=test_data["test_code"],
                        test_name=test_data["test_name"],
                        source_code=test_data["source_code"]
                    )
                    session.add_job(job)
                else:
                    logger.warning(f"❌ Test ID {test_id} not found in database")
            
            if not session.jobs:
                raise ValueError("No valid tests found for execution")
            
            # Store session
            self.active_sessions[session_id] = session
            
            logger.info(f"✅ Created batch session {session_id} with {len(session.jobs)} tests")
            logger.info(f"📊 Config: {max_parallel} parallel containers, {timeout}s timeout")
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating batch session: {str(e)}")
            raise
    
    async def execute_batch(self, session_id: str) -> Dict[str, Any]:
        """
        Execute all tests in a batch session with parallel processing
        
        Args:
            session_id: Batch session ID
            
        Returns:
            Execution results
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        if session.status != ExecutionStatus.PENDING:
            raise ValueError(f"Session {session_id} is already {session.status.value}")
        
        session.status = ExecutionStatus.RUNNING
        session.start_time = datetime.now()
        
        logger.info(f"🚀 Starting batch execution for session {session_id}")
        logger.info(f"📦 Executing {session.total_tests} tests with {session.max_parallel} parallel containers")
        
        try:
            # Execute jobs in parallel batches
            semaphore = asyncio.Semaphore(session.max_parallel)
            
            async def execute_single_job(job: TestExecutionJob):
                async with semaphore:
                    await self._execute_job(job, session)
            
            # Run all jobs concurrently
            tasks = [execute_single_job(job) for job in session.jobs]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update session status
            session.end_time = datetime.now()
            session.status = ExecutionStatus.COMPLETED
            session.update_statistics()
            
            # Save results to database
            await self._save_batch_results(session)
            
            logger.info(f"✅ Batch execution completed for session {session_id}")
            logger.info(f"📊 Results: {session.completed} passed, {session.failed} failed")
            
            return session.get_results()
            
        except Exception as e:
            logger.error(f"Batch execution error: {str(e)}")
            session.status = ExecutionStatus.FAILED
            session.end_time = datetime.now()
            raise
    
    async def _execute_job(self, job: TestExecutionJob, session: BatchExecutionSession):
        """Execute a single test job in Docker container"""
        try:
            job.status = ExecutionStatus.RUNNING
            job.start_time = datetime.now()
            session.update_statistics()
            
            logger.info(f"🐳 Executing job {job.job_id}: {job.test_name}")
            
            # Execute in Docker
            result = await docker_executor.execute_test_in_container(
                test_code=job.test_code,
                language=session.language,
                additional_packages=session.additional_packages,
                timeout=session.timeout
            )
            
            job.end_time = datetime.now()
            
            if result.get("success"):
                job.status = ExecutionStatus.COMPLETED
                job.result = {
                    "output": result.get("output", ""),
                    "exit_code": result.get("exit_code", 0)
                }
                logger.info(f"✅ Job {job.job_id} completed successfully")
            else:
                job.status = ExecutionStatus.FAILED
                job.error = result.get("error", "Unknown error")
                job.result = {
                    "output": result.get("output", ""),
                    "exit_code": result.get("exit_code", -1)
                }
                logger.warning(f"❌ Job {job.job_id} failed: {job.error}")
            
            session.update_statistics()
            
        except Exception as e:
            logger.error(f"Job execution error for {job.job_id}: {str(e)}")
            job.status = ExecutionStatus.FAILED
            job.error = str(e)
            job.end_time = datetime.now()
            session.update_statistics()
    
    async def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """Get current progress of a batch session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        return session.get_progress()
    
    async def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get detailed results of a batch session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        return session.get_results()
    
    async def cancel_session(self, session_id: str):
        """Cancel a running batch session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.status = ExecutionStatus.CANCELLED
        session.end_time = datetime.now()
        
        logger.info(f"⚠️ Cancelled batch session {session_id}")
    
    async def _save_batch_results(self, session: BatchExecutionSession):
        """Save batch execution results to database"""
        try:
            db = await get_database()
            collection = db["session_history"]
            
            record = {
                "session_id": session.session_id,
                "timestamp": datetime.now().isoformat(),
                "processes": {
                    "parallel_docker_execution": {
                        "status": session.status.value,
                        "timestamp": session.start_time.isoformat() if session.start_time else None,
                        "process_name": session.process_name,
                        "configuration": {
                            "language": session.language,
                            "max_parallel": session.max_parallel,
                            "timeout": session.timeout,
                            "additional_packages": session.additional_packages
                        },
                        "statistics": {
                            "total_tests": session.total_tests,
                            "completed": session.completed,
                            "failed": session.failed,
                            "success_rate": round((session.completed / session.total_tests * 100) if session.total_tests > 0 else 0, 1)
                        },
                        "execution_time": {
                            "start": session.start_time.isoformat() if session.start_time else None,
                            "end": session.end_time.isoformat() if session.end_time else None,
                            "total_seconds": (session.end_time - session.start_time).total_seconds() if (session.start_time and session.end_time) else None
                        },
                        "results": [job.to_dict() for job in session.jobs]
                    }
                }
            }
            
            await collection.insert_one(record)
            logger.info(f"✅ Saved batch execution results: {session.session_id}")
            
        except Exception as e:
            logger.error(f"Error saving batch results: {str(e)}")

# Global instance
parallel_docker_executor = ParallelDockerExecutor()
