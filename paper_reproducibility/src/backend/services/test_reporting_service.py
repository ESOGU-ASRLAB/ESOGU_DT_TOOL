"""
test_reporting_service.py
Comprehensive Test Reporting Service
Handles multi-process analysis, chunking, and AI-powered report generation
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import re
from core.database import get_database
from services.quality_metrics_calculator import quality_calculator
from services.report_quality_evaluator import report_quality_evaluator

logger = logging.getLogger(__name__)


class TestReportingService:
    """
    Service for generating comprehensive test reports from STLC processes
    """
    
    # Process configuration: max items per chunk
    # Optimized for ~4000 tokens per chunk (≈16000 characters)
    CHUNK_SIZES = {
        "test_scenario_generation": 100,  # 100 scenarios per chunk
        "test_case_generation": 200,      # 200 test cases per chunk
        "test_case_optimization": 150,    # 150 optimized cases per chunk
        "test_code_generation": 150,      # 150 test codes per chunk
        "test_execution": 150,            # 150 execution results per chunk
        "default": 100
    }
    
    # Maximum character size per chunk (≈4000 tokens)
    MAX_CHUNK_CHARS = 16000
    
    def __init__(self):
        self.db = None
        self._cached_prompt = None
    
    async def initialize(self):
        """Initialize database connection"""
        if self.db is None:
            self.db = await get_database()
    
    async def get_test_reporting_prompt(self) -> Dict[str, str]:
        """
        Get test reporting prompt from database
        Returns prompt_text and system_suffix
        """
        if self._cached_prompt:
            return self._cached_prompt
        
        await self.initialize()
        
        # Try to fetch from MongoDB
        try:
            # Use synchronous database access
            from core.database import get_db
            db = get_db()
            prompt_doc = db.test_reporting_prompt.find_one({"process_type": "test_reporting"})
            
            if prompt_doc:
                self._cached_prompt = {
                    "prompt_text": prompt_doc.get("prompt_text", ""),
                    "system_suffix": prompt_doc.get("system_suffix", "")
                }
                logger.info("✅ Loaded test reporting prompt from database")
                return self._cached_prompt
        except Exception as e:
            logger.warning(f"Could not load prompt from database: {e}")
        
        # Fallback to default
        logger.warning("Using default hardcoded prompt (database prompt not found)")
        return None
    
    async def fetch_available_sessions(
        self, 
        process_names: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        include_test_reports: bool = False  # NEW: Control whether to include test reporting sessions
    ) -> List[Dict[str, Any]]:
        """
        Fetch available sessions from session_history
        
        Args:
            process_names: Filter by specific process names
            date_from: ISO date string (e.g., "2025-11-01")
            date_to: ISO date string
            include_test_reports: If False, exclude test reporting sessions (default: False)
            
        Returns:
            List of session summaries with process counts
        """
        await self.initialize()
        collection = self.db["session_history"]
        
        # Build query
        query = {}
        
        # Exclude test reporting sessions by default (they are generated reports, not source sessions)
        if not include_test_reports:
            query["session_type"] = {"$ne": "test_reporting"}
        
        # Date filter (MongoDB uses 'created_at' field)
        if date_from or date_to:
            query["created_at"] = {}
            if date_from:
                query["created_at"]["$gte"] = date_from
            if date_to:
                query["created_at"]["$lte"] = date_to
        
        # Fetch all matching sessions (sort by created_at descending)
        cursor = collection.find(query).sort("created_at", -1)
        sessions = await cursor.to_list(length=None)
        
        # Process and enrich session data
        result = []
        for session in sessions:
            # Try session_id first, fallback to _id
            session_id = session.get("session_id") or str(session.get("_id", "unknown"))
            # MongoDB stores timestamp in either 'created_at' or 'timestamp' field
            created_at = session.get("created_at") or session.get("timestamp", "")
            processes = session.get("processes", {})
            
            # Filter by process names if specified
            if process_names:
                processes = {k: v for k, v in processes.items() if k in process_names}
            
            # Count available processes and collect detailed metadata
            process_summary = {}
            process_details = []
            models_used = set()
            
            for process_name, process_data in processes.items():
                if isinstance(process_data, dict) and process_data.get("output"):
                    # Count items in output (scenarios, cases, etc.)
                    output = process_data.get("output", {})
                    count = self._count_process_items(process_name, output)
                    process_summary[process_name] = count
                    
                    # Get model used from process data (check multiple locations)
                    model_used = (
                        process_data.get("model_used") or 
                        process_data.get("model_name") or 
                        process_data.get("model") or
                        process_data.get("used_model") or
                        process_data.get("input", {}).get("model_name") or
                        process_data.get("input", {}).get("model")
                    )
                    
                    # Collect detailed metadata for each process
                    detail = {
                        "type": process_name,
                        "timestamp": process_data.get("timestamp"),
                        "model": model_used,  # Can be None
                        "edited_prompt": process_data.get("edited_prompt", False),
                        "item_count": count
                    }
                    
                    # Add process-specific fields
                    if process_name == "test_scenario_generation":
                        detail.update({
                            "category": process_data.get("selected_category"),
                            "test_type": process_data.get("selected_test_type"),
                            "process_title": process_data.get("process_title")
                        })
                    elif process_name == "test_case_generation":
                        detail.update({
                            "based_on": process_data.get("selected_process_title"),
                            "updated_at": process_data.get("updated_at")
                        })
                    elif process_name == "test_code_generation":
                        # Get process name from different possible locations
                        input_data = process_data.get("input", {})
                        detail.update({
                            "process_name": process_data.get("process_name"),
                            "code_generation_process_name": process_data.get("code_generation_process_name") or input_data.get("process_title"),
                            "model_used": process_data.get("model_used") or input_data.get("model_name"),
                            "framework": process_data.get("output", {}).get("environment_info", {}).get("framework"),
                            "language": process_data.get("output", {}).get("environment_info", {}).get("language")
                        })
                    elif process_name == "test_execution":
                        # Get execution metadata
                        input_data = process_data.get("input", {})
                        output_data = process_data.get("output", {})
                        exec_results = output_data.get("execution_results", {})
                        detail.update({
                            "process_name": process_data.get("process_name"),
                            "code_generation_process_name": input_data.get("code_generation_process_name"),
                            "model_used": process_data.get("model_used") or output_data.get("model_used"),
                            "success": output_data.get("success", False),
                            "total_tests": exec_results.get("total_tests", 0),
                            "passed": exec_results.get("passed", 0),
                            "failed": exec_results.get("failed", 0),
                            "success_rate": exec_results.get("success_rate", 0.0)
                        })
                    elif process_name == "code_review":
                        detail.update({
                            "prompt_length": len(process_data.get("used_prompt", ""))
                        })
                    elif process_name == "requirement_analysis":
                        detail.update({
                            "prompt_length": len(process_data.get("used_prompt", ""))
                        })
                    elif process_name == "test_planning":
                        detail.update({
                            "prompt_length": len(process_data.get("used_prompt", ""))
                        })
                    
                    process_details.append(detail)
                    
                    # Track unique models used
                    if detail["model"]:
                        models_used.add(detail["model"])
            
            if process_summary:  # Only include sessions with data
                # Get process_name, fallback to process_title if available
                process_name_display = session.get("process_name")
                
                # If no process_name, try to extract from processes
                if not process_name_display:
                    # Check for process_title in any process
                    for proc_name, proc_data in processes.items():
                        if isinstance(proc_data, dict):
                            process_title = proc_data.get("process_title")
                            if process_title:
                                process_name_display = process_title
                                break
                
                # Format timestamp to ISO format if it's a datetime object
                formatted_timestamp = created_at
                if hasattr(created_at, 'isoformat'):
                    formatted_timestamp = created_at.isoformat()
                
                result.append({
                    "session_id": session_id,
                    "timestamp": formatted_timestamp,
                    "process_name": process_name_display or None,
                    "processes": process_summary,
                    "process_details": process_details,  # NEW: Detailed process metadata
                    "models_used": list(models_used)  # NEW: Unique models used in session
                })
        
        return result
    
    def _count_process_items(self, process_name: str, output: Dict[str, Any]) -> int:
        """Count items in a process output"""
        logger.info(f"Counting items for process: {process_name}")
        logger.debug(f"Output keys: {list(output.keys()) if output else 'None'}")
        
        if process_name == "test_scenario_generation":
            scenarios = output.get("test_scenarios", {})
            if isinstance(scenarios, dict):
                scenarios = scenarios.get("TestScenarios", [])
            return len(scenarios) if isinstance(scenarios, list) else 0
        
        elif process_name == "test_case_generation":
            # Handle multiple formats - check most common format first
            # Format 1: output.test_case_results (most common - direct)
            test_case_results = output.get("test_case_results", [])
            if test_case_results:
                total = sum(len(result.get("test_cases", [])) for result in test_case_results)
                return total
            
            # Format 2: data.test_case_results (nested in data)
            data = output.get("data", {})
            test_case_results = data.get("test_case_results", [])
            if test_case_results:
                total = sum(len(result.get("test_cases", [])) for result in test_case_results)
                return total
            
            # Format 3: test_cases (flat list)
            test_cases = output.get("test_cases", [])
            return len(test_cases) if isinstance(test_cases, list) else 0
        
        elif process_name == "test_case_optimization":
            # Try multiple possible keys
            optimized_cases = output.get("optimized_test_cases", [])
            if not optimized_cases:
                data = output.get("data", {})
                optimized_cases = data.get("optimized_results", [])
            return len(optimized_cases) if isinstance(optimized_cases, list) else 0
        
        elif process_name == "test_code_generation":
            # Try multiple possible paths
            generated_tests = output.get("generated_tests", [])
            if not generated_tests:
                # Try data.generated_tests path
                data = output.get("data", {})
                generated_tests = data.get("generated_tests", [])
            
            count = len(generated_tests) if isinstance(generated_tests, list) else 0
            logger.info(f"test_code_generation count: {count}")
            return count
        
        elif process_name == "test_execution":
            # Try to get execution results
            execution_results = output.get("execution_results", {})
            if execution_results:
                total = execution_results.get("total_tests", 0)
                if total > 0:
                    logger.info(f"test_execution count from execution_results: {total}")
                    return total
            
            # Fallback: Count from terminal output
            terminal_output = output.get("terminal_output", "")
            if "Total Tests:" in terminal_output:
                match = re.search(r'Total Tests: (\d+)', terminal_output)
                if match:
                    count = int(match.group(1))
                    logger.info(f"test_execution count from terminal_output: {count}")
                    return count
            
            # Check if we have test_results array
            test_results = output.get("test_results", [])
            if isinstance(test_results, list) and test_results:
                logger.info(f"test_execution count from test_results: {len(test_results)}")
                return len(test_results)
            
            logger.info(f"test_execution: output exists, returning 1")
            return 1  # At least one execution if output exists
        
        # Default: check if output exists
        return 1 if output else 0
    
    async def fetch_session_data(
        self, 
        session_id: str, 
        selected_processes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch specific session data for selected processes
        
        Args:
            session_id: Session ID to fetch
            selected_processes: List of process names to include (None = all processes)
            
        Returns:
            Dictionary with session metadata and process data
        """
        await self.initialize()
        collection = self.db["session_history"]
        
        # Fetch session document
        session = await collection.find_one({"session_id": session_id})
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Extract process data
        processes_data = session.get("processes", {})
        selected_data = {}
        
        # If selected_processes is None, fetch all processes
        if selected_processes is None:
            process_names = list(processes_data.keys())
        else:
            process_names = selected_processes
        
        for process_name in process_names:
            if process_name in processes_data:
                process_data = processes_data[process_name]
                output = process_data.get("output", {})
                
                # Calculate objective quality metrics
                quality_metrics = quality_calculator.calculate_process_quality(
                    process_name, 
                    output
                )
                
                selected_data[process_name] = {
                    "input": process_data.get("input", {}),
                    "output": output,
                    "metadata": process_data.get("metadata", {}),
                    "timestamp": process_data.get("timestamp", ""),
                    "quality_metrics": quality_metrics  # NEW: Objective quality scores
                }
        
        return {
            "session_id": session_id,
            "session_timestamp": session.get("timestamp", ""),
            "process_name": session.get("process_name", ""),
            "processes": selected_data
        }
    
    def create_chunks(
        self, 
        process_name: str, 
        process_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create chunks from process data based on smart chunking strategy
        
        Args:
            process_name: Name of the process
            process_data: Process output data
            
        Returns:
            List of chunks with metadata
        """
        output = process_data.get("output", {})
        chunks = []
        
        # Get chunk size for this process type
        chunk_size = self.CHUNK_SIZES.get(process_name, self.CHUNK_SIZES["default"])
        
        # Process-specific chunking
        if process_name == "test_scenario_generation":
            scenarios = output.get("test_scenarios", {})
            if isinstance(scenarios, dict):
                scenarios = scenarios.get("TestScenarios", [])
            # Ensure scenarios is a list (not None)
            if not isinstance(scenarios, list):
                scenarios = []
            chunks = self._chunk_list(scenarios, chunk_size, "scenarios")
        
        elif process_name == "test_case_generation":
            # Handle multiple formats - check most common format first
            # Format 1: output.test_case_results (most common - direct)
            test_case_results = output.get("test_case_results", [])
            if test_case_results:
                # Flatten all test cases
                all_cases = []
                for result in test_case_results:
                    all_cases.extend(result.get("test_cases", []))
                chunks = self._chunk_list(all_cases, chunk_size, "test_cases")
            else:
                # Format 2: data.test_case_results (nested in data)
                data = output.get("data", {})
                test_case_results = data.get("test_case_results", [])
                if test_case_results:
                    # Flatten all test cases
                    all_cases = []
                    for result in test_case_results:
                        all_cases.extend(result.get("test_cases", []))
                    chunks = self._chunk_list(all_cases, chunk_size, "test_cases")
                else:
                    # Format 3: test_cases (flat list)
                    test_cases = output.get("test_cases", [])
                    if isinstance(test_cases, list):
                        chunks = self._chunk_list(test_cases, chunk_size, "test_cases")
                    else:
                        chunks = []
        
        elif process_name == "test_case_optimization":
            # Handle both old and new formats
            optimized_cases = output.get("optimized_test_cases", [])
            data = output.get("data", {})
            metadata = output.get("metadata", {})
            
            if not optimized_cases:
                optimized_cases = data.get("optimized_results", [])
            
            # Ensure optimized_cases is a list
            if not isinstance(optimized_cases, list):
                optimized_cases = []
            
            # Get counts from metadata or calculate
            before_count = metadata.get("original_count", output.get("original_count", 0))
            after_count = metadata.get("optimized_count", len(optimized_cases))
            
            if before_count == 0 and "total_test_cases" in output:
                before_count = output.get("total_test_cases", 0)
            
            chunks = self._chunk_list(optimized_cases, chunk_size, "optimized_cases")
            # Add metadata to each chunk
            for chunk in chunks:
                chunk["optimization_metadata"] = {
                    "before_count": before_count,
                    "after_count": after_count,
                    "reduction_count": before_count - after_count,
                    "reduction_percentage": ((before_count - after_count) / before_count * 100) if before_count > 0 else 0
                }
        
        elif process_name == "test_code_generation":
            generated_tests = output.get("generated_tests", [])
            # Ensure generated_tests is a list
            if not isinstance(generated_tests, list):
                generated_tests = []
            chunks = self._chunk_list(generated_tests, chunk_size, "generated_tests")
        
        elif process_name == "test_execution":
            # For execution, use the full terminal output
            terminal_output = output.get("terminal_output", "")
            chunks = [{
                "chunk_index": 0,
                "total_chunks": 1,
                "data_type": "execution_output",
                "data": terminal_output,
                "metadata": {
                    "model_used": output.get("model_used", "unknown"),
                    "timestamp": output.get("timestamp", "")
                }
            }]
        
        else:
            # Generic chunking: convert output to JSON string and chunk by size
            output_str = json.dumps(output, indent=2)
            chunks = self._chunk_by_size(output_str, self.MAX_CHUNK_CHARS, "generic_output")
        
        # Add process name to all chunks
        for chunk in chunks:
            chunk["process_name"] = process_name
        
        return chunks
    
    def _chunk_list(
        self, 
        items: List[Any], 
        chunk_size: int, 
        data_type: str
    ) -> List[Dict[str, Any]]:
        """Chunk a list into smaller lists"""
        # Safety check: ensure items is a list (not None or other types)
        if items is None or not isinstance(items, list):
            logger.warning(f"_chunk_list received non-list items: {type(items).__name__}. Returning empty list.")
            return []
        
        # Handle empty list
        if len(items) == 0:
            return []
        
        chunks = []
        total_chunks = (len(items) + chunk_size - 1) // chunk_size  # Ceiling division
        
        for i in range(0, len(items), chunk_size):
            chunk_items = items[i:i + chunk_size]
            chunks.append({
                "chunk_index": len(chunks),
                "total_chunks": total_chunks,
                "data_type": data_type,
                "data": chunk_items,
                "item_count": len(chunk_items)
            })
        
        return chunks
    
    def _chunk_by_size(
        self, 
        text: str, 
        max_size: int, 
        data_type: str
    ) -> List[Dict[str, Any]]:
        """Chunk text by character size"""
        # Safety check: ensure text is a string
        if text is None or not isinstance(text, str):
            logger.warning(f"_chunk_by_size received non-string text: {type(text).__name__}. Returning empty list.")
            return []
        
        # Handle empty string
        if len(text) == 0:
            return []
        
        chunks = []
        total_chunks = (len(text) + max_size - 1) // max_size
        
        for i in range(0, len(text), max_size):
            chunk_text = text[i:i + max_size]
            chunks.append({
                "chunk_index": len(chunks),
                "total_chunks": total_chunks,
                "data_type": data_type,
                "data": chunk_text,
                "char_count": len(chunk_text)
            })
        
        return chunks
    
    def create_intermediate_prompt(
        self, 
        chunk: Dict[str, Any],
        analysis_depth: str = "detailed"
    ) -> str:
        """
        Create analysis prompt for a single chunk
        
        Args:
            chunk: Chunk data with metadata
            analysis_depth: "summary" | "detailed" | "deep"
            
        Returns:
            Formatted prompt for LLM
        """
        process_name = chunk.get("process_name", "unknown")
        data_type = chunk.get("data_type", "unknown")
        chunk_index = chunk.get("chunk_index", 0)
        total_chunks = chunk.get("total_chunks", 1)
        
        # Base context
        prompt = f"""You are an expert Test Manager analyzing STLC (Software Testing Life Cycle) process data.

**Process:** {process_name.replace('_', ' ').title()}
**Data Type:** {data_type}
**Chunk:** {chunk_index + 1} of {total_chunks}

"""
        
        # Add specific instructions based on process type
        if process_name == "test_scenario_generation":
            prompt += """Analyze these test scenarios and provide:

1. **Key Metrics:**
   - Total scenarios in this chunk
   - Test types distribution
   - Coverage areas

2. **Quality Indicators:**
   - Scenario completeness (have clear preconditions, steps, expected results)
   - Scenario depth and detail level
   - Edge case coverage

3. **Notable Patterns:**
   - Common test types
   - Testing focus areas
   - Any gaps or missing coverage

4. **Issues or Concerns:**
   - Unclear or ambiguous scenarios
   - Missing critical test areas
   - Duplicate or redundant scenarios

"""
        
        elif process_name == "test_case_generation":
            prompt += """Analyze these test cases and provide:

1. **Key Metrics:**
   - Total test cases in this chunk
   - Test case complexity distribution
   - Coverage metrics

2. **Quality Indicators:**
   - Test case clarity and completeness
   - Test data specifications
   - Expected results precision

3. **Notable Patterns:**
   - Common test case types
   - Testing approach (positive/negative/boundary)
   - Requirement traceability

4. **Issues or Concerns:**
   - Missing test data
   - Unclear assertions
   - Potential gaps in coverage

"""
        
        elif process_name == "test_case_optimization":
            optimization_meta = chunk.get("optimization_metadata", {})
            prompt += f"""Analyze these optimized test cases and provide:

**Optimization Context:**
- Before: {optimization_meta.get('before_count', 'N/A')} test cases
- After: {optimization_meta.get('after_count', 'N/A')} test cases
- Reduction: {optimization_meta.get('reduction_percentage', 0):.1f}%

1. **Optimization Impact:**
   - Quality of reduction (appropriate vs over-optimized)
   - Coverage preservation
   - Critical test case retention

2. **Quality Indicators:**
   - Redundancy elimination effectiveness
   - Essential test case preservation
   - Edge case handling

3. **Notable Patterns:**
   - Types of test cases removed
   - Consolidation strategies used
   - Coverage optimization approach

4. **Issues or Concerns:**
   - Potentially over-aggressive optimization
   - Missing critical edge cases
   - Coverage gaps introduced

"""
        
        elif process_name == "test_code_generation":
            prompt += """Analyze these generated test codes and provide:

1. **Key Metrics:**
   - Total test codes in this chunk
   - Programming language/framework used
   - Code structure quality

2. **Quality Indicators:**
   - Code readability and maintainability
   - Test framework usage
   - Assertion quality

3. **Notable Patterns:**
   - Common testing patterns used
   - Code organization approach
   - Test data handling

4. **Issues or Concerns:**
   - Code quality issues
   - Missing assertions or validations
   - Potential runtime errors

"""
        
        elif process_name == "test_execution":
            prompt += """Analyze these test execution results and provide:

1. **Key Metrics:**
   - Total tests executed
   - Pass/fail statistics
   - Success rate

2. **Quality Indicators:**
   - Execution reliability
   - Error patterns
   - Performance metrics

3. **Notable Patterns:**
   - Common failure types
   - Success patterns
   - Execution stability

4. **Issues or Concerns:**
   - Critical failures
   - Flaky tests
   - Performance bottlenecks

"""
        
        else:
            prompt += f"""Analyze this {process_name} data and provide:

1. Key metrics and statistics
2. Quality indicators
3. Notable patterns
4. Issues or concerns

"""
        
        # Add the actual data
        data = chunk.get("data")
        if isinstance(data, (list, dict)):
            data_str = json.dumps(data, indent=2)
        else:
            data_str = str(data)
        
        # Truncate if too long (safety measure)
        if len(data_str) > 100000:
            data_str = data_str[:100000] + "\n\n... (truncated for length)"
        
        # Analysis depth instructions
        depth_instruction = ""
        if analysis_depth == "summary":
            depth_instruction = "\n**Analysis Level: SUMMARY** - Provide only high-level key findings and critical metrics. Be concise.\n"
        elif analysis_depth == "detailed":
            depth_instruction = "\n**Analysis Level: DETAILED** - Provide comprehensive analysis with supporting data and examples. This is the recommended level.\n"
        elif analysis_depth == "deep":
            depth_instruction = "\n**Analysis Level: DEEP** - Provide in-depth analysis with extensive insights, patterns, edge cases, and detailed recommendations.\n"
        
        prompt += f"""
{depth_instruction}
**Data to Analyze:**

```json
{data_str}
```

Please provide analysis according to the specified analysis level, focusing on the points above.
"""
        
        return prompt
    
    async def create_final_synthesis_prompt(
        self,
        intermediate_summaries: List[Dict[str, Any]],
        session_metadata: Dict[str, Any],
        analysis_depth: str = "detailed",
        raw_session_data: List[Dict[str, Any]] = None
    ) -> str:
        """
        Create final synthesis prompt from all intermediate summaries
        Supports both single session and multi-session comparison
        Uses database prompt if available, falls back to hardcoded
        
        Args:
            intermediate_summaries: List of {session_id, process, chunk_index, summary} dicts
            session_metadata: Session info (can contain multiple sessions)
            analysis_depth: Level of analysis
            raw_session_data: Optional raw session data for direct LLM access
            
        Returns:
            Final synthesis prompt
        """
        # Safety checks
        if intermediate_summaries is None:
            intermediate_summaries = []
        if raw_session_data is None:
            raw_session_data = []
        if session_metadata is None:
            session_metadata = {}
        
        # Try to get database prompt
        db_prompt = await self.get_test_reporting_prompt()
        if db_prompt and db_prompt.get("prompt_text"):
            # Use database prompt with variable substitution
            return await self._create_prompt_from_template(
                db_prompt,
                intermediate_summaries,
                session_metadata,
                analysis_depth,
                raw_session_data
            )
        
        # Fallback to hardcoded prompt
        logger.info("Using hardcoded prompt template")
        comparison_mode = session_metadata.get("comparison_mode", False)
        
        if comparison_mode:
            # Multi-session comparison mode
            sessions = session_metadata.get("sessions", [])
            
            # Safety check
            if not sessions:
                logger.warning("No sessions metadata provided, using session IDs only")
                sessions = [{"session_id": sid, "process_name": sid, "session_timestamp": ""} 
                           for sid in session_metadata.get("session_ids", [])]
            
            # Group summaries by session and process
            session_summaries = {}
            for summary in intermediate_summaries:
                session_id = summary.get("session_id", "unknown")
                process = summary.get("process_name", "unknown")
                
                if session_id not in session_summaries:
                    session_summaries[session_id] = {}
                if process not in session_summaries[session_id]:
                    session_summaries[session_id][process] = []
                    
                session_summaries[session_id][process].append(summary.get("summary", ""))
            
            # Build comparison prompt
            # Safe len() calls with defensive checks
            session_count = len(sessions) if sessions and isinstance(sessions, list) else 0
            
            # Safely get unique process names
            try:
                process_names = set()
                if intermediate_summaries and isinstance(intermediate_summaries, list):
                    for s in intermediate_summaries:
                        if s and isinstance(s, dict):
                            process_names.add(s.get('process_name', 'unknown'))
                process_count = len(process_names)
            except Exception as e:
                logger.warning(f"Error counting processes: {e}")
                process_count = 0
            
            prompt = f"""You are a Senior Test Manager creating a comprehensive STLC **COMPARISON REPORT** across multiple test sessions.

**Comparison Overview:**
- Number of Sessions: {session_count}
- Total Processes Analyzed: {process_count}

**Sessions Being Compared:**
"""
            # Safe iteration over sessions
            if sessions and isinstance(sessions, list):
                for i, session in enumerate(sessions, 1):
                    if session and isinstance(session, dict):
                        prompt += f"\n{i}. **{session.get('process_name', 'Unnamed')}**\n"
                        prompt += f"   - Session ID: {session.get('session_id', 'N/A')}\n"
                        prompt += f"   - Date: {session.get('session_timestamp', 'N/A')}\n"
            
            prompt += """
You have received BOTH raw session data AND intermediate analysis summaries for maximum context.

---

## RAW SESSION DATA (For Your Reference)

"""
            
            # Add raw session data for detailed analysis
            if raw_session_data and isinstance(raw_session_data, list):
                for session_info in raw_session_data:
                    if not session_info or not isinstance(session_info, dict):
                        continue
                    session_id = session_info.get("session_id", "unknown")
                    session_data = session_info.get("data", {})
                    session_name = session_data.get("process_name", session_id)
                    
                    prompt += f"\n### Session: {session_name}\n"
                    prompt += f"- **Session ID**: {session_id}\n"
                    prompt += f"- **Timestamp**: {session_data.get('session_timestamp', 'N/A')}\n"
                    processes = session_data.get('processes', {})
                    process_count = len(processes) if processes and isinstance(processes, dict) else 0
                    prompt += f"- **Processes**: {process_count}\n\n"
                    
                    # Add process-level metrics
                    for process_name, process_data in session_data.get("processes", {}).items():
                        output = process_data.get("output", {})
                        metadata = process_data.get("metadata", {})
                        
                        prompt += f"#### {process_name.replace('_', ' ').title()}\n"
                        
                        # Extract key metrics based on process type
                        if process_name == "requirement_analysis":
                            requirements = output.get("requirements", [])
                            req_count = len(requirements) if requirements and isinstance(requirements, list) else 0
                            prompt += f"- Requirements Analyzed: {req_count}\n"
                            
                        elif process_name == "test_scenario_generation":
                            scenarios = output.get("test_scenarios", [])
                            scenario_count = len(scenarios) if scenarios and isinstance(scenarios, list) else 0
                            prompt += f"- Scenarios Generated: {scenario_count}\n"
                            if scenarios and isinstance(scenarios, list) and len(scenarios) > 0:
                                # Count by category if available
                                categories = {}
                                for scenario in scenarios:
                                    cat = scenario.get("category", "Unknown")
                                    categories[cat] = categories.get(cat, 0) + 1
                                prompt += f"- Categories: {', '.join(f'{k}({v})' for k, v in categories.items())}\n"
                        
                        elif process_name == "test_case_generation":
                            # Handle new format
                            test_cases = output.get("test_cases", [])
                            data = output.get("data", {})
                            
                            if not test_cases and data:
                                test_case_results = data.get("test_case_results", [])
                                all_cases = []
                                for result in test_case_results:
                                    all_cases.extend(result.get("test_cases", []))
                                test_cases = all_cases
                            
                            total_cases = len(test_cases)
                            prompt += f"- Test Cases Generated: {total_cases}\n"
                            
                            if test_cases and isinstance(test_cases, list):
                                # Count positive vs negative
                                positive = 0
                                negative = 0
                                for tc in test_cases:
                                    title = tc.get("Title", "").lower()
                                    test_type = tc.get("test_type", "").lower()
                                    if "invalid" in title or "error" in title or "negative" in title or test_type == "negative":
                                        negative += 1
                                    else:
                                        positive += 1
                                
                                prompt += f"- Positive/Negative: {positive}/{negative}\n"
                                ratio = f"{positive/negative:.1f}:1" if negative > 0 else "All positive"
                                prompt += f"- Test Balance Ratio: {ratio}\n"
                                
                                # Count by complexity if available
                                with_steps = sum(1 for tc in test_cases if tc.get("Steps"))
                                with_data = sum(1 for tc in test_cases if tc.get("TestData"))
                                prompt += f"- Cases with Steps: {with_steps}\n"
                                prompt += f"- Cases with Test Data: {with_data}\n"
                        
                        elif process_name == "test_case_optimization":
                            # Handle both new and old formats
                            data = output.get("data", {})
                            metadata = output.get("metadata", {})
                            
                            # Get optimization results
                            optimized_results = data.get("optimized_results", [])
                            unique_cases = output.get("unique_test_cases", [])
                            similar_cases = output.get("similar_test_cases", [])
                            
                            # Use old format if new format not available
                            if not optimized_results and unique_cases:
                                optimized_results = unique_cases
                            
                            # Get counts
                            original_count = metadata.get("original_count", output.get("total_test_cases", 0))
                            optimized_count = metadata.get("optimized_count", len(optimized_results))
                            
                            # Old format: total = unique + similar
                            if original_count == 0 and (unique_cases or similar_cases):
                                original_count = len(unique_cases) + len(similar_cases)
                                optimized_count = len(unique_cases)
                            
                            # Calculate metrics
                            removed_count = original_count - optimized_count
                            reduction_rate = (removed_count / original_count * 100) if original_count > 0 else 0
                            
                            prompt += f"\n📊 **Test Case Optimization Metrics:**\n"
                            prompt += f"- Original Test Cases: {original_count}\n"
                            
                            # Old format specifics
                            if unique_cases or similar_cases:
                                prompt += f"  - Unique Cases: {len(unique_cases)}\n"
                                prompt += f"  - Similar/Duplicate Cases: {len(similar_cases)}\n"
                            
                            prompt += f"- Optimized (Selected) Test Cases: {optimized_count}\n"
                            prompt += f"- Test Cases Removed: {removed_count}\n"
                            prompt += f"- Optimization Rate: {reduction_rate:.1f}%\n"
                            prompt += f"- Efficiency Gain: {reduction_rate:.1f}% fewer tests needed\n"
                            
                            # Add rationale summary if available
                            if optimized_results:
                                with_rationale = sum(1 for r in optimized_results if r.get("optimization_rationale"))
                                if with_rationale > 0:
                                    prompt += f"- Cases with Rationale: {with_rationale}/{len(optimized_results)}\n"
                        
                        elif process_name == "test_code_generation":
                            tests = output.get("generated_tests", [])
                            prompt += f"- Test Code Files Generated: {len(tests)}\n"
                        
                        # Add objective quality metrics
                        quality_metrics = process_data.get("quality_metrics", {})
                        if quality_metrics:
                            prompt += f"\n**Objective Quality Metrics (Calculated):**\n"
                            prompt += f"- Overall Score: {quality_metrics.get('score', 'N/A')}/10\n"
                            prompt += f"- Completeness: {quality_metrics.get('completeness', 'N/A')}/10\n"
                            prompt += f"- Clarity: {quality_metrics.get('clarity', 'N/A')}/10\n"
                            prompt += f"- Coverage: {quality_metrics.get('coverage', 'N/A')}/10\n"
                            prompt += f"- Depth: {quality_metrics.get('depth', 'N/A')}/10\n"
                            
                            calc_details = quality_metrics.get('calculation_details', {})
                            if calc_details:
                                prompt += f"- Calculation Details: {json.dumps(calc_details, indent=2)}\n"
                        
                        # Add model info
                        model_used = metadata.get("model_used", "Unknown")
                        prompt += f"- Model Used: {model_used}\n"
                        prompt += f"- Timestamp: {process_data.get('timestamp', 'N/A')}\n\n"
            
            prompt += """
---

## INTERMEDIATE ANALYSIS SUMMARIES

The following are AI-generated summaries of the above raw data:

"""
            
            # Add summaries organized by session
            if session_summaries and isinstance(session_summaries, dict):
                for session_id, processes in session_summaries.items():
                    if not processes or not isinstance(processes, dict):
                        continue
                    session_info = next((s for s in (sessions or []) if s and isinstance(s, dict) and s.get('session_id') == session_id), {})
                    prompt += f"\n### Session: {session_info.get('process_name', session_id)}\n\n"
                
                for process_name, summaries in processes.items():
                    prompt += f"#### {process_name.replace('_', ' ').title()}\n\n"
                    for i, summary in enumerate(summaries, 1):
                        if len(summaries) > 1:
                            prompt += f"**Part {i}:**\n{summary}\n\n"
                        else:
                            prompt += f"{summary}\n\n"
            
            prompt += """
---

## YOUR TASK: Generate ISTQB & IEEE 829 Compliant Test Report

Use BOTH the raw data metrics AND the intermediate summaries to create your comprehensive test report.

**Standards Compliance:**
- ✅ ISTQB Test Management Standards
- ✅ IEEE 829-2008 Test Documentation
- ✅ ISO/IEC/IEEE 29119 Software Testing

## Required Test Report Structure (IEEE 829 & ISTQB Compliant)

Generate your report following this exact structure with clear sections:

---

### 1. 📋 TEST SUMMARY (IEEE 829 Section 1 | ISTQB Test Manager)

**Report Identification:**
- Report ID: `TEST-RPT-[Date]-[Session]`
- Report Version: 1.0
- Test Sessions Analyzed: [List session IDs]
- Report Generation Date: [Date]
- Generated By: STLC Manager AI System

**Test Objectives & Scope:**
- Testing scope and objectives for each session
- Test completion criteria defined
- Overall test mission statement

**Executive Summary:**
- Overall test status and completion percentage
- Key achievements and highlights from testing
- Critical issues and blockers identified
- Go/No-Go recommendation with justification
- Risk summary and quality assessment

---

### 2. 📊 TEST METRICS & COVERAGE ANALYSIS (ISTQB Foundation | IEEE 829 Section 2)

**Test Execution Metrics:**
- Total test cases: [Planned] vs [Executed]
- Test execution progress: [X]%
- Pass rate: [X]% | Fail rate: [Y]%
- Test efficiency: [cases/day or hour]
- Test case distribution: Positive vs Negative

**Test Coverage Analysis:**
- Requirements coverage: [X]%
- Test scenario coverage: [X scenarios across Y categories]
- Functional area coverage matrix
- Boundary value and edge case coverage
- Risk-based coverage assessment

**Quality Metrics (ISO/IEC/IEEE 29119):**
- Test case quality score: [X]/10
- Test completeness: [X]/10
- Test clarity: [X]/10
- Test depth: [X]/10

---

### 3. 🐛 DEFECT SUMMARY & ANALYSIS (IEEE 829 Section 3)

---

### 3. 🐛 DEFECT SUMMARY & ANALYSIS (IEEE 829 Section 3)

**Defect Statistics:**
- Total defects identified: [X]
- Defects by severity: Critical ([X]) | High ([Y]) | Medium ([Z]) | Low ([W])
- Defects by type: Functional | Performance | Security | Usability
- Defect detection rate: [defects per test case]
- Defect removal efficiency: [X]%

**Defect Distribution:**
- Defects by functional area (table format)
- Defects by test phase
- Root cause categories

**Defect Trends:**
- Open vs Closed defects over time
- Defect aging analysis
- Fix verification status

---

### 4. 🎯 TEST COMPLETION CRITERIA ASSESSMENT (ISTQB Test Manager)

**Entry Criteria Status:**
- Were all entry criteria met? (Yes/No with details)
- Any deviations from entry criteria and their impact

**Exit Criteria Evaluation:**
- ✅ Test coverage targets: [Met/Not Met] - [X]% achieved (target: [Y]%)
- ✅ Defect closure criteria: [Met/Not Met] - [X]% closed (target: [Y]%)
- ✅ Performance criteria: [Met/Not Met]
- ✅ Quality gates: [Pass/Fail] with details

**Completion Assessment:**
- Overall completion percentage: [X]%
- Outstanding items preventing full completion
- Risks accepted for release (if any)
- Recommendations for sign-off

---

### 5. 🔄 DETAILED SESSION ANALYSIS (Process-by-Process)

For each analyzed session, provide:

**Session: [Session Name/ID]**
- **Session Metadata:** Date, Duration, Scope
- **Test Objectives:** What was tested and why
- **Processes Executed:**
  - 📋 Requirement Analysis: [Summary]
  - 🎯 Test Scenario Generation: [Summary]
  - 📝 Test Case Generation: [Summary]
  - ⚡ Test Case Optimization: [Summary]
  - 💻 Test Code Generation: [Summary]
  - 🚀 Test Execution: [Summary]
- **Key Findings:** Notable observations from this session
- **Issues & Blockers:** Any problems encountered
- **Session Quality Score:** [X]/10

---

### 6. 📈 COMPARATIVE ANALYSIS & TRENDS (ISTQB Advanced - Multi-Session Only)

**Cross-Session Metrics:**
- Test case generation efficiency trends
- Quality improvement/regression patterns
- Coverage evolution across sessions
- Defect detection rate trends

**Process Efficiency:**
- Test design efficiency: [metrics]
- Test execution efficiency: [metrics]
- Optimization effectiveness: [before/after metrics]
- Process improvement opportunities identified

**Best Practices Identified:**
- Successful strategies from analysis
- Recommended approaches for future testing
- Areas for process improvement

---

### 7. ⚠️ RISK ASSESSMENT & MITIGATION (ISTQB Risk-Based Testing)

**Product Quality Risks:**
- Identified quality risks with severity (High/Medium/Low)
- Risk likelihood and impact analysis
- Risk mitigation status
- Residual risks remaining

**Project Risks:**
- Schedule risks identified
- Resource constraints and risks
- Technical debt and risks
- Environmental risks

**Risk-Based Testing Coverage:**
- High-risk areas coverage: [X]%
- Medium-risk areas coverage: [Y]%
- Low-risk areas coverage: [Z]%
- Risk vs test effort allocation matrix

**Risk Mitigation Recommendations:**
- Priority actions to address high risks
- Suggested additional testing focus areas
- Resource allocation recommendations

---

### 8. 💡 RECOMMENDATIONS & ACTION ITEMS (IEEE 829 Section 8)

**Test Process Improvements:**
- Process optimization opportunities identified
- Tool and automation recommendations
- Training needs for team members
- Best practices to adopt in future cycles

**Product Quality Actions:**
- Critical defects requiring immediate attention
- Quality improvement areas with action plans
- Performance optimization needs
- Technical debt items to address

**Next Steps & Action Plan:**

| Priority | Action Item | Owner | Timeline | Success Criteria |
|----------|-------------|-------|----------|------------------|
| High | [Action] | [Team] | [Date] | [Criteria] |
| Medium | [Action] | [Team] | [Date] | [Criteria] |
| Low | [Action] | [Team] | [Date] | [Criteria] |

---

### 9. 📚 APPENDICES & SUPPORTING DATA (IEEE 829)

**A. Detailed Test Metrics Tables**
- Complete test execution logs
- Test case execution details
- Defect list with full details

**B. Test Environment Configuration**
- Environment specifications used
- Tools and versions
- Test data sets used

**C. Standards Reference**
- ISTQB Foundation Level principles applied
- ISTQB Test Manager techniques used
- IEEE 829-2008 section mapping
- ISO/IEC/IEEE 29119-3 compliance details

---

## 🏆 FINAL COMPLIANCE VERIFICATION

This report complies with:
- ✅ **ISTQB Foundation Level**: All basic testing terminology and metrics follow ISTQB definitions
- ✅ **ISTQB Test Manager**: Advanced techniques for test management, risk assessment, and strategic analysis applied
- ✅ **IEEE 829-2008**: All 8 required sections present with appropriate content
- ✅ **ISO/IEC/IEEE 29119-3**: Modern test documentation practices followed

**Report Signature:**
- Generated by: STLC Manager AI System
- Standards Applied: ISTQB Foundation/Test Manager, IEEE 829-2008, ISO/IEC/IEEE 29119-3
- Confidence Level: [High/Medium] based on data completeness
- Validity Period: [Date Range]

---

## OUTPUT FORMAT REQUIREMENTS

**CRITICAL:** Generate a clean, professional Markdown report following the structure above.

**DO NOT return JSON format. Return ONLY the Markdown document.**

**Formatting Guidelines:**
- Use clear heading hierarchy (##, ###, ####)
- Include emoji icons for main sections (📋, 📊, 🐛, 🎯, etc.)
- Create well-formatted tables using Markdown syntax
- Use bullet points and numbered lists appropriately
- Add horizontal rules (---) to separate major sections
- Use **bold** for emphasis on key metrics
- Use > blockquotes for important notes or warnings
- Keep language professional, objective, and data-driven

**Example of correct output format:**
```markdown
# 📊 Comprehensive Test Report
*Generated: 2026-01-12 | Version: 1.0*

---

## 📘 Standards Compliance Declaration
...
```

Generate a complete, professionally formatted Markdown document now:
"""
            
            return prompt
        
        else:
            # Single session mode - use single session prompt
            logger.info("Creating single session prompt")
            
            # Get the first (and only) session data
            if raw_session_data and isinstance(raw_session_data, list) and len(raw_session_data) > 0:
                session_info = raw_session_data[0]
                session_data = {
                    "metadata": {
                        "session_id": session_info.get("session_id", ""),
                        "session_timestamp": session_info.get("data", {}).get("session_timestamp", ""),
                        "process_name": session_info.get("data", {}).get("process_name", "")
                    },
                    "raw_data": raw_session_data,
                    "summaries": intermediate_summaries
                }
                
                return self.create_single_session_prompt(
                    session_data=session_data,
                    analysis_depth=analysis_depth
                )
            else:
                logger.warning("No raw session data available for single session prompt")
                # Fallback: create a basic prompt
                return self._create_fallback_prompt(intermediate_summaries, session_metadata, analysis_depth)
    
    def _create_fallback_prompt(
        self,
        intermediate_summaries: List[Dict[str, Any]],
        session_metadata: Dict[str, Any],
        analysis_depth: str
    ) -> str:
        """Fallback prompt when no raw data is available"""
        session_ids = session_metadata.get("session_ids", [])
        session_id = session_ids[0] if session_ids and isinstance(session_ids, list) and len(session_ids) > 0 else "Unknown"
        
        prompt = f"""You are a Senior Test Manager creating a comprehensive STLC report.

**Session ID:** {session_id}
**Analysis Depth:** {analysis_depth}

## Analysis Summaries

"""
        
        for summary in intermediate_summaries:
            process = summary.get("process_name", "unknown")
            summary_text = summary.get("summary", "")
            prompt += f"\n### {process.replace('_', ' ').title()}\n\n{summary_text}\n\n"
        
        prompt += """
---

Based on the above analysis summaries, generate a comprehensive ISTQB & IEEE 829 compliant test report.

Include:
- Executive summary
- Test metrics and coverage
- Key findings
- Recommendations

Generate a complete, professionally formatted Markdown document now:
"""
        
        return prompt
    
    def create_single_session_prompt(
        self,
        session_data: Dict[str, Any],
        analysis_depth: str = "detailed"
    ) -> str:
        """
        Create prompt for single session analysis
        
        Args:
            session_data: Single session data with processes
            analysis_depth: Level of analysis detail
            
        Returns:
            Formatted prompt string
        """
        session_metadata = session_data.get("metadata", {})
        raw_session_data = session_data.get("raw_data", [])
        intermediate_summaries = session_data.get("summaries", [])
        
        # Group summaries by process
        process_summaries = {}
        for summary in intermediate_summaries:
            process = summary.get("process_name", "unknown")
            if process not in process_summaries:
                process_summaries[process] = []
            process_summaries[process].append(summary.get("summary", ""))
        
        # Build prompt
        prompt = f"""You are a Senior Test Manager creating a comprehensive STLC report.

**Session Information:**
- Session ID: {session_metadata.get('session_id', 'N/A')}
- Date: {session_metadata.get('session_timestamp', 'N/A')}
- Process Name: {session_metadata.get('process_name', 'N/A')}
- Processes Analyzed: {len(process_summaries)}

You have received BOTH raw session data AND intermediate analysis summaries.

---

## RAW SESSION DATA (For Your Reference)

"""
        
        # Add raw session data if provided (single session)
        if raw_session_data and len(raw_session_data) > 0:
            session_info = raw_session_data[0]
            session_data_inner = session_info.get("data", {})
            
            for process_name, process_data in session_data_inner.get("processes", {}).items():
                output = process_data.get("output", {})
                metadata = process_data.get("metadata", {})
                
                prompt += f"\n### {process_name.replace('_', ' ').title()}\n"
                
                # Extract key metrics
                if process_name == "requirement_analysis":
                    requirements = output.get("requirements", [])
                    req_count = len(requirements) if requirements and isinstance(requirements, list) else 0
                    prompt += f"- Requirements Analyzed: {req_count}\n"
                    
                elif process_name == "test_scenario_generation":
                    scenarios = output.get("test_scenarios", [])
                    scenario_count = len(scenarios) if scenarios and isinstance(scenarios, list) else 0
                    prompt += f"- Scenarios Generated: {scenario_count}\n"
                    
                elif process_name == "test_case_generation":
                    # Handle new format
                    test_cases = output.get("test_cases", [])
                    data = output.get("data", {})
                    
                    if not test_cases and data:
                        test_case_results = data.get("test_case_results", [])
                        all_cases = []
                        for result in test_case_results:
                            all_cases.extend(result.get("test_cases", []))
                        test_cases = all_cases
                        
                        total_cases = len(test_cases)
                        prompt += f"- Test Cases Generated: {total_cases}\n"
                        
                        if test_cases and isinstance(test_cases, list):
                            # Count positive/negative
                            positive = 0
                            negative = 0
                            for tc in test_cases:
                                title = tc.get("Title", "").lower()
                                test_type = tc.get("test_type", "").lower()
                                if any(word in title for word in ["invalid", "error", "negative", "fail"]) or test_type == "negative":
                                    negative += 1
                                else:
                                    positive += 1
                            
                            prompt += f"- Positive/Negative: {positive}/{negative}\n"
                            ratio = f"{positive/negative:.1f}:1" if negative > 0 else "All positive"
                            prompt += f"- Test Balance: {ratio}\n"
                    
                    elif process_name == "test_case_optimization":
                        # Handle new format
                        data = output.get("data", {})
                        metadata = output.get("metadata", {})
                        
                        original_count = metadata.get("original_count", output.get("total_test_cases", 0))
                        optimized_count = metadata.get("optimized_count", 0)
                        
                        if optimized_count == 0:
                            optimized_results = data.get("optimized_results", [])
                            optimized_count = len(optimized_results)
                        
                        # Also try old format
                        if original_count == 0:
                            unique_cases = output.get("unique_test_cases", [])
                            similar_cases = output.get("similar_test_cases", [])
                            unique = len(unique_cases) if unique_cases and isinstance(unique_cases, list) else 0
                            similar = len(similar_cases) if similar_cases and isinstance(similar_cases, list) else 0
                            original_count = unique + similar
                            optimized_count = unique
                        
                        removed = original_count - optimized_count
                        reduction = (removed / original_count * 100) if original_count > 0 else 0
                        
                        prompt += f"- Original: {original_count}, Selected: {optimized_count}, Removed: {removed} ({reduction:.1f}% reduction)\n"
                    
                    elif process_name == "test_code_generation":
                        tests = output.get("generated_tests", [])
                        prompt += f"- Test Code Files: {len(tests)}\n"
                    
                    prompt += f"- Model: {metadata.get('model_used', 'Unknown')}\n\n"
            
            prompt += """
---

## INTERMEDIATE ANALYSIS SUMMARIES

The following are AI-generated summaries of the above raw data:

"""
            
            # Add each process summary
            for process_name, summaries in process_summaries.items():
                prompt += f"\n### {process_name.replace('_', ' ').title()}\n\n"
                for i, summary in enumerate(summaries, 1):
                    if len(summaries) > 1:
                        prompt += f"**Part {i}:**\n{summary}\n\n"
                    else:
                        prompt += f"{summary}\n\n"
            
            prompt += """
---

## YOUR TASK: Generate ISTQB & IEEE 829 Compliant Single-Session Test Report

Use BOTH the raw data metrics AND the intermediate summaries to create your comprehensive test report.

**Standards Compliance:**
- ✅ ISTQB Test Management Standards (Foundation & Test Manager)
- ✅ IEEE 829-2008 Test Documentation
- ✅ ISO/IEC/IEEE 29119 Software Testing

**Start your report with:**
```
# 📊 Single Session Test Report
*Session: [Session ID] | Generated: [Date] | Version: 1.0*

---

## 📘 Standards Compliance Declaration

This test report has been prepared in compliance with the following international testing standards:

| Standard | Version/Level | Purpose | Applied Sections |
|----------|---------------|---------|------------------|
| **ISTQB Foundation Level** | Foundation | Basic test reporting concepts | Test process methodology, Basic metrics, Quality indicators |
| **ISTQB Test Manager** | Advanced | Advanced test management | Management reporting, Risk assessment, Quality analysis |
| **IEEE 829-2008** | 2008 | Test documentation standards | Test summary, Metric reporting, Documentation |
| **ISO/IEC/IEEE 29119-3** | Part 3 | Modern test documentation | Quality metrics, Modern methodology compliance |

---
```

## Required Single-Session Test Report Structure

### 1. 📋 TEST SUMMARY (IEEE 829 Section 1)

**Report Identification:**
- Report ID and session details
- Test objectives and scope
- Report status

**Executive Summary:**
- Overall test completion and quality
- Key achievements
- Critical findings
- Effectiveness assessment

### 2. 📊 TEST METRICS & RESULTS (ISTQB Foundation)

**Test Execution Metrics:**
- Total test artifacts created
- Quality scores per process
- Efficiency metrics
- Coverage statistics

**Process-Specific Results:**
For each STLC process analyzed:
- Process objectives achieved
- Quantitative metrics
- Quality assessment
- Effectiveness rating

### 3. 🎯 QUALITY ASSESSMENT (ISTQB)

**Objective Quality Metrics:**
- Completeness score (0-10)
- Clarity and documentation (0-10)
- Coverage adequacy (0-10)
- Overall quality rating (0-10)

**Quality Indicators:**
- Test artifact quality
- Process adherence
- Best practices compliance
- Areas of excellence

### 4. 📈 PROCESS BREAKDOWN

For each analyzed STLC process:
- **Process Name & Scope**
- **Key Deliverables**
- **Quantitative Metrics**
- **Quality Evaluation**
- **Strengths Identified**
- **Improvement Areas**
- **Process Recommendations**

### 5. ⚠️ RISK ASSESSMENT (ISTQB Risk-Based Testing)

**Identified Risks:**
- Quality risks
- Coverage gaps
- Process weaknesses
- Technical concerns

**Risk Mitigation:**
- Recommended actions
- Priority levels
- Resource requirements
- Expected outcomes

### 6. 💡 RECOMMENDATIONS & ACTION ITEMS (IEEE 829)

**Immediate Actions (High Priority):**
- Critical improvements needed
- Quick wins available
- Blocker resolutions

**Short-Term Improvements:**
- Process enhancements
- Quality improvements
- Tool/automation needs

**Long-Term Strategic Actions:**
- Process maturity improvements
- Capability building
- Best practice adoption

### 7. 📊 METRICS DASHBOARD

**Summary Table:**
| Process | Artifacts | Quality Score | Coverage | Status |
|---------|-----------|--------------|----------|---------|
| ...     | ...       | .../10       | ...%     | ✅/⚠️   |

**Trend Indicators:**
- Process efficiency trends
- Quality evolution
- Coverage progression

### 8. 📋 APPENDICES (IEEE 829)

**Supporting Documentation:**
- Detailed metrics
- Test artifacts summary
- Environment details
- Model and tool information

---

**Reporting Standards Applied:**
- 📘 ISTQB Foundation Level (Test Reporting)
- 📘 IEEE 829-2008 (Test Documentation)
- 📘 ISO/IEC/IEEE 29119-3 (Test Documentation)

---

## OUTPUT FORMAT: Structured JSON

Please provide the report in the following JSON structure:

```json
{
  "report_metadata": {
    "report_id": "string",
    "session_id": "string",
    "generation_date": "ISO date",
    "standards_applied": ["ISTQB", "IEEE 829", "ISO/IEC/IEEE 29119"],
    "analysis_depth": "string"
  },
  "sections": {
    "test_summary": {
      "title": "TEST SUMMARY",
      "icon": "📋",
      "content": "markdown content...",
      "key_metrics": {
        "overall_quality": number,
        "completion_status": "string"
      }
    },
    "test_metrics": {
      "title": "TEST METRICS & RESULTS",
      "icon": "📊",
      "content": "markdown content..."
    },
    "quality_assessment": {
      "title": "QUALITY ASSESSMENT",
      "icon": "🎯",
      "content": "markdown content...",
      "scores": {
        "completeness": number,
        "clarity": number,
        "coverage": number,
        "overall": number
      }
    },
    "process_breakdown": {
      "title": "PROCESS BREAKDOWN",
      "icon": "📈",
      "content": "markdown content..."
    },
    "risk_assessment": {
      "title": "RISK ASSESSMENT",
      "icon": "⚠️",
      "content": "markdown content..."
    },
    "recommendations": {
      "title": "RECOMMENDATIONS & ACTION ITEMS",
      "icon": "💡",
      "content": "markdown content..."
    },
    "metrics_dashboard": {
      "title": "METRICS DASHBOARD",
      "icon": "📊",
      "content": "markdown content..."
    },
    "appendices": {
      "title": "APPENDICES",
      "icon": "📋",
      "content": "markdown content..."
    }
  },
  "full_report_markdown": "Complete markdown version for fallback..."
---

**Reporting Standards Applied:**
- 📘 ISTQB Foundation Level (Test Reporting)
- 📘 IEEE 829-2008 (Test Documentation)
- 📘 ISO/IEC/IEEE 29119-3 (Test Documentation)

---

**📚 STANDARDS COMPLIANCE TABLE**

Include this table in your report (in Appendices section) to show which standards were applied:

| Standard | Version/Level | Purpose | Coverage Areas |
|----------|---------------|---------|----------------|
| **ISTQB Foundation Level** | Foundation | Basic test reporting concepts and terminology | - Test process methodology<br>- Basic metric definitions<br>- Test completion criteria<br>- Basic quality indicators |
| **ISTQB Test Manager** | Advanced | Advanced test management and strategic reporting | - Management-level reporting<br>- Risk-based test assessment<br>- Comparative analysis<br>- Trend analysis and forecasting<br>- Resource optimization recommendations |
| **IEEE 829-2008** | 2008 | Test documentation structure and content standards | - Report section structure (8 main sections)<br>- Test summary format<br>- Metric reporting templates<br>- Appendix and reference management<br>- Formal documentation requirements |
| **ISO/IEC/IEEE 29119-3** | Part 3 (Test Documentation) | Modern test documentation best practices | - Current documentation approaches<br>- Flexible report structures<br>- Quality assessment metrics<br>- Agile/modern methodology compliance<br>- International compatibility |

---

## OUTPUT FORMAT REQUIREMENTS

**CRITICAL:** Generate a clean, professional Markdown report following the structure above.

**Formatting Guidelines:**
- Use clear heading hierarchy (##, ###, ####)
- Include emoji icons for main sections (📋, 📊, 🎯, etc.)
- Create well-formatted tables using Markdown syntax
- Use bullet points and numbered lists appropriately
- Add horizontal rules (---) to separate major sections
- Use professional Markdown formatting
- Include quantitative metrics and scores
- Use standardized terminology
- Provide visual tables and comparisons
- Reference applicable standards
- Use bullet points for lists
- Highlight critical items with ⚠️ or 🔴
- Highlight positive items with ✅ or 🟢

**Start your report with:**
```
# 📊 Test Session Report
*Standards: ISTQB Foundation, IEEE 829-2008, ISO/IEC/IEEE 29119-3*

---
```

**Analysis Depth Level: {analysis_depth.upper()}**
"""
            if analysis_depth == "summary":
                prompt += """
- Provide HIGH-LEVEL overview only
- Focus on critical findings and key metrics
- Keep sections concise (2-3 key points each)
- Prioritize executive summary and top recommendations
"""
            elif analysis_depth == "detailed":
                prompt += """
- Provide COMPREHENSIVE analysis with supporting data (RECOMMENDED)
- Include specific examples and evidence
- Balance breadth and depth across all sections
- Provide detailed process breakdown and metrics
"""
            elif analysis_depth == "deep":
                prompt += """
- Provide IN-DEPTH investigation with extensive insights
- Deep dive into each process with pattern analysis
- Include edge cases, anomalies, and detailed examples
- Extensive quality assessment and recommendations
- Implementation-ready action plans
"""
            
            prompt += """
Generate the comprehensive report now.
"""
        
        return prompt
    
    async def save_report(
        self,
        session_ids: List[str],
        report_content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Save generated report as a NEW independent session in session_history.
        This allows multiple reports for the same sessions with different models/depths.
        
        Args:
            session_ids: List of analyzed session IDs (source sessions)
            report_content: Generated report markdown
            metadata: Report metadata (processes, model, tokens, etc.)
            
        Returns:
            New session ID for the test reporting session
        """
        await self.initialize()
        collection = self.db["session_history"]
        
        # Generate unique session_id for this test reporting session
        timestamp = datetime.now()
        session_id = f"test_report_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Create descriptive process name
        session_count = len(session_ids)
        model_name = metadata.get("model", "Unknown")
        analysis_depth = metadata.get("analysis_depth", "detailed")
        
        process_name = f"Test Report: {session_count} Session(s) - {model_name} ({analysis_depth})"
        
        # Build the new session document as an INDEPENDENT session
        session_document = {
            "session_id": session_id,
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "process_name": process_name,
            "session_type": "test_reporting",  # Mark as test reporting session
            
            # Metadata about the reporting process
            "reporting_metadata": {
                "analyzed_session_ids": session_ids,
                "session_count": session_count,
                "model_used": model_name,
                "analysis_depth": analysis_depth,
                "report_generated_at": timestamp.isoformat(),
                "process_names_analyzed": metadata.get("process_names", []),
                "total_chunks": metadata.get("total_chunks", 0),
                "total_tokens_estimated": metadata.get("total_tokens", 0)
            },
            
            # Store the report as a process output (consistent with other sessions)
            "processes": {
                "test_reporting": {
                    "status": "completed",
                    "timestamp": timestamp.isoformat(),
                    "process_name": "Test Report Generation",
                    "model_used": model_name,
                    
                    "input": {
                        "session_ids": session_ids,
                        "session_count": session_count,
                        "analysis_depth": analysis_depth,
                        "process_names": metadata.get("process_names", [])
                    },
                    
                    "output": {
                        "success": True,
                        "report_content": report_content,
                        "report_length": len(report_content),
                        "generated_at": timestamp.isoformat()
                    },
                    
                    "metadata": {
                        "model_used": model_name,
                        "total_chunks": metadata.get("total_chunks", 0),
                        "intermediate_summaries": metadata.get("intermediate_summaries", 0),
                        "total_tokens_estimated": metadata.get("total_tokens", 0),
                        "generation_time_seconds": metadata.get("generation_time", 0)
                    }
                }
            }
        }
        
        # Insert as a NEW session document
        await collection.insert_one(session_document)
        
        logger.info(f"✅ Test report saved as new independent session: {session_id}")
        logger.info(f"   - Analyzed sessions: {session_count}")
        logger.info(f"   - Model: {model_name}")
        logger.info(f"   - Analysis depth: {analysis_depth}")
        logger.info(f"   - Report length: {len(report_content)} characters")
        
        return session_id
    
    async def _create_prompt_from_template(
        self,
        db_prompt: Dict[str, str],
        intermediate_summaries: List[Dict[str, Any]],
        session_metadata: Dict[str, Any],
        analysis_depth: str,
        raw_session_data: List[Dict[str, Any]]
    ) -> str:
        """
        Create prompt from database template with variable substitution
        
        Args:
            db_prompt: Database prompt with prompt_text and system_suffix
            intermediate_summaries: Analysis summaries
            session_metadata: Session information
            analysis_depth: Analysis level
            raw_session_data: Raw session data
            
        Returns:
            Formatted prompt with all variables substituted
        """
        prompt_template = db_prompt.get("prompt_text", "")
        
        # Prepare session data
        session_count = session_metadata.get("session_count", len(session_metadata.get("session_ids", [])))
        session_ids = session_metadata.get("session_ids", [])
        
        # Extract process types
        process_types = set()
        for summary in intermediate_summaries:
            process_types.add(summary.get("process_name", "unknown"))
        process_types_str = ", ".join(sorted(process_types))
        
        # Format date range
        date_range = "N/A"
        if session_metadata.get("date_from") or session_metadata.get("date_to"):
            date_from = session_metadata.get("date_from", "Start")
            date_to = session_metadata.get("date_to", "End")
            date_range = f"{date_from} to {date_to}"
        
        # Format raw session data
        session_data_str = json.dumps(raw_session_data, indent=2, default=str)
        
        # Format intermediate summaries
        intermediate_summaries_str = ""
        for i, summary in enumerate(intermediate_summaries, 1):
            session_id = summary.get("session_id", "unknown")
            process = summary.get("process_name", "unknown")
            chunk_idx = summary.get("chunk_index", 0)
            summary_text = summary.get("summary", "")
            
            intermediate_summaries_str += f"""
### Summary {i}
- **Session**: {session_id}
- **Process**: {process}
- **Chunk**: {chunk_idx + 1}

{summary_text}

---
"""
        
        # Substitute variables
        # Note: intermediate_summaries is prepared but not currently used in the template
        # Keeping the code for potential future use
        prompt = prompt_template.format(
            analysis_depth=analysis_depth,
            session_count=session_count,
            process_types=process_types_str,
            date_range=date_range,
            session_data=session_data_str
        )
        
        return prompt


# Singleton instance
test_reporting_service = TestReportingService()
