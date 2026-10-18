"""
Test Code Generation Service
---------------------------
Generates executable test code based on unique test cases, source code, and environment setup
"""

import json
import logging
import asyncio
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.database import get_db
from utils.model_client import LLMClient
from utils.file_handler import FileHandler
from utils.text_processor import TextProcessor
from utils.text_splitter import count_tokens
from utils.standalone_test_validation import (
    STANDALONE_REMOTE_REQUIREMENTS,
)
from services.test_code_oracle import ORACLE_PROMPT_REQUIREMENTS, evaluate_test_code
from services.robot_capability_service import (
    capability_descriptor,
    capability_prompt_context,
    validate_generated_code_against_capabilities,
)
from utils.standalone_test_validation import supports_legacy_sim_robot_goal
from services.project_structure_service import (
    EXECUTION_GROUNDING_RULES,
    project_structure_prompt_context,
    validate_code_against_project_structure,
)

logger = logging.getLogger(__name__)


def _first_value(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Return the first present, non-empty value from mixed legacy/new schemas."""
    for key in keys:
        value = data.get(key)
        if value is not None and value != "":
            return value
    return default


def _generation_result_reason(result: Optional[Dict[str, Any]]) -> str:
    """Return the most useful human-readable reason carried by a result."""
    if not result:
        return "The model returned no generation result."
    return str(
        result.get("error")
        or result.get("eligibility_reason")
        or result.get("unsupported_reason")
        or "No diagnostic reason was provided."
    )


def _is_retryable_generation_result(result: Optional[Dict[str, Any]]) -> bool:
    """Retry transient model/API failures that were normalized into result dicts."""
    if not result or result.get("status") != "error":
        return False
    reason = _generation_result_reason(result).lower()
    return any(
        marker in reason
        for marker in (
            "timeout",
            "timed out",
            "no response",
            "server_error",
            "engine protocol",
            "peg-native format",
            "503",
            "unavailable",
            "connection",
            "temporarily",
        )
    )


class TestCodeGenerationService:
    def __init__(self):
        self.db = get_db()
        self.session_collection = self.db["session_history"]
        self.file_handler = FileHandler()
        self.text_processor = TextProcessor()
        
    def get_environment_setups(self) -> List[Dict[str, Any]]:
        """
        Veritabanından environment_setup sonuçlarını getirir
        """
        try:
            logger.info(f"Database: {self.db.name}, Collection: {self.session_collection.name}")
            
            # Veritabanında kaç kayıt var kontrol et
            total_records = self.session_collection.count_documents({})
            step_records = self.session_collection.count_documents({"step": "environment_setup"})
            logger.info(f"Total records in session_history: {total_records}")
            logger.info(f"Records with step='environment_setup': {step_records}")
            # Use nested processes structure: processes.environment_setup
            pipeline = [
                {"$match": {"processes.environment_setup": {"$exists": True}}},
                {"$project": {
                    "session_id": 1,
                    "timestamp": "$processes.environment_setup.timestamp",
                    "setup_result": "$processes.environment_setup.output",
                    "environment_name": "$processes.environment_setup.environment_name",
                    "process_name": {"$literal": "Environment Setup"}
                }},
                {"$sort": {"timestamp": -1}}
            ]
            
            try:
                results = list(self.session_collection.aggregate(pipeline))
                logger.info(f"Found {len(results)} results from environment_setup query")
                
                # İlk 3 sonucu logla
                for i, result in enumerate(results[:3], 1):
                    env_name = result.get("environment_name", "NOT_SET")
                    proc_name = result.get("process_name", "NOT_SET")
                    logger.info(f"Result {i}: env={env_name}, proc={proc_name}, session={result.get('session_id', 'N/A')}")
            except Exception as agg_error:
                logger.error(f"Aggregation error: {str(agg_error)}")
                results = []
            
            formatted_results = []
            for result in results:
                session_id = result.get("session_id", "Unknown")
                timestamp = result.get("timestamp", "Unknown")
                setup_result = result.get("setup_result", {})
                files_analyzed = result.get("files_analyzed", [])
                environment_name = result.get("environment_name", "Unnamed Environment")
                process_name = result.get("process_name", "Unknown Process")
                
                # Environment setup sonucundan dil ve framework bilgilerini çıkar
                environment_info = self._parse_environment_setup(setup_result)
                
                formatted_results.append({
                    "_id": session_id,  # MongoDB için _id field
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "environment_name": environment_name,
                    "process_name": process_name,
                    "display_name": f"{environment_name} - {environment_info.get('language', 'Unknown')} ({timestamp})",
                    "environment_info": environment_info,
                    "files_analyzed": files_analyzed,
                    "setup_result": setup_result
                })
            
            logger.info(f"Found {len(formatted_results)} environment setup records")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting environment setups: {str(e)}")
            return []
    
    def _parse_environment_setup(self, setup_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Environment setup sonucunu parse ederek dil ve framework bilgilerini çıkarır
        """
        try:
            # Setup result'dan text'i al
            setup_text = ""
            if isinstance(setup_result, list) and setup_result:
                setup_text = setup_result[0].get("setup", "")
            elif isinstance(setup_result, dict):
                setup_text = setup_result.get("setup", "")
            elif isinstance(setup_result, str):
                setup_text = setup_result
            
            # Basit parsing ile dil ve framework tespiti
            environment_info = {
                "language": "unknown",
                "framework": "unknown",
                "dependencies": [],
                "setup_commands": []
            }
            
            setup_lower = setup_text.lower()
            
            # Dil tespiti
            if "python" in setup_lower:
                environment_info["language"] = "python"
                if "pytest" in setup_lower:
                    environment_info["framework"] = "pytest"
                elif "unittest" in setup_lower:
                    environment_info["framework"] = "unittest"
                else:
                    environment_info["framework"] = "pytest"  # Default
            elif "javascript" in setup_lower or "node" in setup_lower:
                environment_info["language"] = "javascript"
                if "jest" in setup_lower:
                    environment_info["framework"] = "jest"
                elif "mocha" in setup_lower:
                    environment_info["framework"] = "mocha"
                else:
                    environment_info["framework"] = "jest"  # Default
            elif "java" in setup_lower:
                environment_info["language"] = "java"
                if "junit" in setup_lower:
                    environment_info["framework"] = "junit"
                else:
                    environment_info["framework"] = "junit"  # Default
            elif "c#" in setup_lower or "csharp" in setup_lower:
                environment_info["language"] = "csharp"
                environment_info["framework"] = "nunit"
            
            return environment_info
            
        except Exception as e:
            logger.error(f"Error parsing environment setup: {str(e)}")
            return {"language": "unknown", "framework": "unknown", "dependencies": [], "setup_commands": []}

    def _infer_environment_from_sources(
        self,
        source_files: List,
        project_structure: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Build a deterministic fallback when no environment-setup step exists."""
        names = [
            str(getattr(item, "filename", None) or getattr(item, "name", ""))
            for item in source_files or []
        ]
        suffixes = {os.path.splitext(name.lower())[1] for name in names}
        language = "python" if ".py" in suffixes else "unknown"
        framework = "pytest" if language == "python" else "unknown"
        dependencies = []
        for file_info in (project_structure or {}).get("files", []):
            if not isinstance(file_info, dict):
                continue
            for dependency in file_info.get("imports", []):
                if isinstance(dependency, str) and dependency not in dependencies:
                    dependencies.append(dependency)
        if language == "python":
            for dependency in ("pytest", "unittest.mock"):
                if dependency not in dependencies:
                    dependencies.append(dependency)
        return {
            "language": language,
            "framework": framework,
            "dependencies": dependencies,
            "setup_commands": ["python -m pytest -q"] if language == "python" else [],
            "source": "inferred_from_source",
            "source_files": names,
        }
    
    def get_unique_test_cases_by_process_title(self, process_title: str) -> List[Dict[str, Any]]:
        """
        Process name'e göre unique test case'leri session_history'den getirir
        Path: session_history->processes->test_case_optimization->output->unique_test_cases
        OR: session_history->processes->test_case_generation->output->test_cases (fallback)
        """
        try:
            # First try: test_case_optimization (optimized test cases)
            query_optimized = {
                "processes.test_case_optimization.process_name": process_title
            }
            
            session = self.session_collection.find_one(query_optimized)
            
            if session:
                test_case_optimization = session.get("processes", {}).get("test_case_optimization", {})
                output = test_case_optimization.get("output", {})
                unique_cases = output.get("unique_test_cases", [])
                
                logger.info(f"Found {len(unique_cases)} unique test cases for process '{process_title}' from test_case_optimization")
                return unique_cases
            
            # Fallback: test_case_generation (generated test cases without optimization)
            logger.info(f"No test_case_optimization found, trying test_case_generation for process '{process_title}'")
            query_generated = {
                "processes.test_case_generation.selected_process_title": process_title
            }
            
            session = self.session_collection.find_one(query_generated)
            
            if session:
                test_case_generation = session.get("processes", {}).get("test_case_generation", {})
                output = test_case_generation.get("output", {})
                
                # Try two formats:
                # 1. New format: test_case_results (array of scenario results)
                test_case_results = output.get("test_case_results", [])
                
                # Extract unique test cases from all scenarios
                unique_cases = []
                for scenario_result in test_case_results:
                    test_cases = scenario_result.get("test_cases", [])
                    for test_case in test_cases:
                        unique_cases.append({
                            "test_case_id": test_case.get("test_case_id") or test_case.get("TestCaseID"),
                            "title": test_case.get("title") or test_case.get("Title"),
                            "scenario_id": test_case.get("scenario_id") or test_case.get("ScenarioID"),
                            "description": test_case.get("description") or test_case.get("Description", ""),
                            "priority": test_case.get("priority") or test_case.get("Priority", "Medium"),
                            "preconditions": test_case.get("preconditions") or test_case.get("Preconditions", []),
                            "steps": test_case.get("steps") or test_case.get("Steps", []),
                            "expected_result": test_case.get("expected_result") or test_case.get("ExpectedResult", ""),
                            "target_symbols": test_case.get("target_symbols") or test_case.get("TargetSymbols", []),
                            "oracle_type": test_case.get("oracle_type") or test_case.get("OracleType", ""),
                            "expected_behavior": test_case.get("expected_behavior") or test_case.get("ExpectedBehavior", "pass"),
                            "execution_status": test_case.get("execution_status") or test_case.get("ExecutionStatus", ""),
                            "unsupported_reason": test_case.get("unsupported_reason") or test_case.get("UnsupportedReason", ""),
                        })
                
                # 2. Old format fallback: test_cases (direct array)
                if not unique_cases:
                    test_cases = output.get("test_cases", [])
                    for test_case in test_cases:
                        unique_cases.append({
                            "test_case_id": test_case.get("test_case_id") or test_case.get("TestCaseID"),
                            "title": test_case.get("title") or test_case.get("Title"),
                            "scenario_id": test_case.get("scenario_id") or test_case.get("ScenarioID"),
                            "description": test_case.get("description") or test_case.get("Description", ""),
                            "priority": test_case.get("priority") or test_case.get("Priority", "Medium"),
                            "preconditions": test_case.get("preconditions") or test_case.get("Preconditions", []),
                            "steps": test_case.get("steps") or test_case.get("Steps", []),
                            "expected_result": test_case.get("expected_result") or test_case.get("ExpectedResult", ""),
                            "target_symbols": test_case.get("target_symbols") or test_case.get("TargetSymbols", []),
                            "oracle_type": test_case.get("oracle_type") or test_case.get("OracleType", ""),
                            "expected_behavior": test_case.get("expected_behavior") or test_case.get("ExpectedBehavior", "pass"),
                            "execution_status": test_case.get("execution_status") or test_case.get("ExecutionStatus", ""),
                            "unsupported_reason": test_case.get("unsupported_reason") or test_case.get("UnsupportedReason", ""),
                        })
                
                logger.info(f"Found {len(unique_cases)} test cases for process '{process_title}' from test_case_generation")
                return unique_cases
            else:
                logger.warning(f"No session found for process name: {process_title} (checked both test_case_optimization and test_case_generation)")
                return []
            
        except Exception as e:
            logger.error(f"Error getting unique test cases: {str(e)}")
            return []
    
    async def analyze_source_code(
        self,
        source_files: List,
        model_name: str = None,
        api_key: str = None,
        max_input_tokens: int = 64000,
    ) -> Dict[str, Any]:
        """
        Yüklenen source code'ları analiz eder
        """
        try:
            if not source_files:
                return {"error": "No source files provided"}
            
            # Dosyaları kaydet ve analiz et
            file_paths = await self.file_handler.save_files(source_files)
            
            code_analysis = {
                "files": [],
                "detected_language": "unknown",
                "structure_analysis": "",
                "imports_dependencies": [],
                "functions_classes": []
            }
            
            all_content = ""
            
            for file_path in file_paths:
                try:
                    content = self.file_handler.read_file(file_path)
                    file_name = file_path.split("/")[-1] if "/" in file_path else file_path.split("\\")[-1]
                    
                    code_analysis["files"].append({
                        "name": file_name,
                        "content": content[:12000],
                        "size": len(content)
                    })
                    
                    all_content += f"\n\n### {file_name} ###\n{content}\n"
                    
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {str(e)}")
            
            # LLM ile kod analizi yap
            if all_content and api_key:
                analysis_prompt = f"""
                Analyze the following source code and provide:
                1. Primary programming language
                2. Code structure (classes, functions, modules)
                3. Import statements and dependencies
                4. Key patterns and frameworks used
                
                Source Code:
                {all_content[:40000]}
                
                Return analysis as JSON:
                {{
                    "detected_language": "python/javascript/java/csharp",
                    "imports_dependencies": ["list", "of", "imports"],
                    "functions_classes": ["main functions and classes"],
                    "structure_analysis": "Brief description of code structure"
                }}
                """
                
                try:
                    analysis_tokens = count_tokens(analysis_prompt)
                    if analysis_tokens > max_input_tokens:
                        raise ValueError(
                            f"Source analysis input requires {analysis_tokens} tokens, exceeding "
                            f"the configured {max_input_tokens}-token budget."
                        )
                    llm_client = LLMClient(model_name=model_name, api_key=api_key, use_case='test_code_generation')
                    analysis_response = await llm_client.generate_response(
                        analysis_prompt,
                        temperature=0.1,
                        max_tokens=8192,
                        skip_chunking=True,
                    )
                    
                    if analysis_response:
                        # JSON parse etmeyi dene
                        try:
                            analysis_data = json.loads(analysis_response)
                            code_analysis.update(analysis_data)
                        except json.JSONDecodeError:
                            logger.warning("Could not parse LLM analysis response as JSON")
                            code_analysis["structure_analysis"] = analysis_response
                            
                except Exception as e:
                    logger.error(f"Error in LLM code analysis: {str(e)}")
            
            # Cleanup temp files
            for file_path in file_paths:
                try:
                    import os
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
            
            return code_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing source code: {str(e)}")
            return {"error": str(e)}
    
    async def generate_test_codes(self, 
                                process_title: str, 
                                environment_session_id: str, 
                                source_files: List, 
                                model_name: str = "llama3.2:3b",
                                custom_prompt: str = None,
                                session_id: str = None,
                                environment_name: str = None,
                                output_format: str = "JSON",
                                api_key: str = None,
                                max_test_cases: int = None,
                                capability_contract: Dict[str, Any] = None,
                                project_structure: Dict[str, Any] = None,
                                max_input_tokens: int = 64000) -> Dict[str, Any]:
        """
        Ana test code generation fonksiyonu
        
        Args:
            max_test_cases: Optional limit on number of test cases to process (for batch processing)
        """
        try:
            if not 4096 <= int(max_input_tokens) <= 64000:
                return {
                    "success": False,
                    "error": "max_input_tokens must be between 4096 and 64000",
                }
            max_input_tokens = int(max_input_tokens)
            # Validate required environment_name
            if not environment_name or environment_name.strip() == "":
                return {
                    "success": False, 
                    "error": "Test Code Generation Process Name is required and cannot be empty"
                }

            logger.info(f"🔍 Debug: Test code generation parameters:")
            logger.info(f"  - process_title: {process_title}")
            logger.info(f"  - environment_session_id: {environment_session_id}")
            logger.info(f"  - session_id: {session_id}")
            logger.info(f"  - environment_name: {environment_name}")
            logger.info(f"  - model_name: {model_name}")
            logger.info(f"  - api_key provided: {'Yes' if api_key else 'No'}")
            logger.info(f"  - max_test_cases: {max_test_cases if max_test_cases else 'unlimited'}")
            
            # 1. Environment setup bilgilerini al
            environment_setups = self.get_environment_setups()
            selected_env = None
            for env in environment_setups:
                if env["session_id"] == environment_session_id:
                    selected_env = env
                    break
            
            if not selected_env:
                inferred_environment = self._infer_environment_from_sources(
                    source_files,
                    project_structure,
                )
                if inferred_environment["language"] == "unknown":
                    return {
                        "success": False,
                        "error": (
                            "Selected environment setup not found and the execution "
                            "environment could not be inferred from the source files"
                        ),
                    }
                selected_env = {
                    "session_id": environment_session_id or "inferred-source-environment",
                    "environment_name": environment_name,
                    "environment_info": inferred_environment,
                }
                logger.info(
                    "No environment setup record found; using deterministic source inference: %s",
                    inferred_environment,
                )
            
            # 2. Unique test case'leri al
            unique_test_cases = self.get_unique_test_cases_by_process_title(process_title)
            if not unique_test_cases:
                return {"success": False, "error": "No unique test cases found for this process"}
            
            # Apply max_test_cases limit if specified
            if max_test_cases and max_test_cases > 0:
                original_count = len(unique_test_cases)
                unique_test_cases = unique_test_cases[:max_test_cases]
                logger.info(f"⚠️ Limited test cases from {original_count} to {len(unique_test_cases)} due to max_test_cases limit")
            
            # 3. Source code'u analiz et
            code_analysis = await self.analyze_source_code(
                source_files,
                model_name,
                api_key,
                max_input_tokens=max_input_tokens,
            )
            if "error" in code_analysis:
                return {"success": False, "error": f"Source code analysis failed: {code_analysis['error']}"}
            
            # 4. Her unique test case için test kodu üret - Gemini API optimizasyonu
            logger.info(f"🤖 Initializing LLM client for model: {model_name}")
            
            # Gemini API için özel timeout ayarları
            is_gemini = 'gemini' in model_name.lower()
            if is_gemini:
                logger.info(f"🔮 Gemini API detected - applying special configurations")
            
            try:
                llm_client = LLMClient(model_name=model_name, api_key=api_key, use_case='test_code_generation')
                logger.info(f"✅ LLM client initialized successfully")
            except Exception as client_error:
                logger.error(f"❌ Failed to initialize LLM client: {str(client_error)}")
                return {"success": False, "error": f"LLM client initialization failed: {str(client_error)}"}
            
            generated_tests = []
            environment_info = selected_env["environment_info"]
            successful_generations = 0
            
            # Process sequentially so local model servers are not overloaded.
            total_cases = len(unique_test_cases)
            logger.info(f"📊 Processing {total_cases} test cases with {model_name}")
            
            for i, test_case in enumerate(unique_test_cases):
                try:
                    logger.info(f"🔄 Generating test code {i+1}/{total_cases}")

                    if str(test_case.get("execution_status", "")).lower() == "unsupported":
                        generated_tests.append({
                            "test_case_id": test_case.get("test_case_id") or test_case.get("TestCaseID", f"TC_{i+1}"),
                            "title": test_case.get("title") or test_case.get("Title", "Unsupported Test"),
                            "status": "unsupported",
                            "execution_eligibility": "unsupported",
                            "eligibility_reason": test_case.get("unsupported_reason") or "The upstream test case is not executable against the declared project API.",
                            "code": None,
                            "repair_attempted": False,
                        })
                        continue
                    
                    # _generate_single_test_code normalizes API exceptions into a
                    # result dictionary. Retry those transient results here as well
                    # as exceptions; otherwise the old loop never retried timeouts.
                    # Local OpenAI-compatible servers can also fail transiently while
                    # decoding a structured response. Give every provider the same
                    # bounded per-case retry budget; deterministic oracle failures are
                    # not retried here.
                    max_retries = 3
                    retry_count = 0
                    test_code = None

                    while retry_count < max_retries:
                        retry_count += 1
                        attempt_started = time.perf_counter()
                        try:
                            test_code = await self._generate_single_test_code(
                                test_case, 
                                code_analysis, 
                                environment_info, 
                                llm_client,
                                i + 1,
                                custom_prompt,
                                capability_contract,
                                project_structure,
                                max_input_tokens,
                            )
                            elapsed_seconds = time.perf_counter() - attempt_started
                            if _is_retryable_generation_result(test_code) and retry_count < max_retries:
                                logger.warning(
                                    "test_code_generation retry case=%s index=%s/%s attempt=%s/%s "
                                    "elapsed=%.1fs reason=%s",
                                    _first_value(test_case, "TestCaseID", "test_case_id", default=f"TC_{i+1}"),
                                    i + 1,
                                    total_cases,
                                    retry_count,
                                    max_retries,
                                    elapsed_seconds,
                                    _generation_result_reason(test_code),
                                )
                                await asyncio.sleep(min(2 ** retry_count, 4))
                                continue

                            if not test_code:
                                test_code = {
                                    "test_case_id": _first_value(
                                        test_case, "TestCaseID", "test_case_id", default=f"TC_{i+1}"
                                    ),
                                    "title": _first_value(test_case, "Title", "title", default="Unknown Test"),
                                    "status": "error",
                                    "error": "The model returned no generation result.",
                                    "code": None,
                                }
                            test_code["generation_attempts"] = retry_count
                            generated_tests.append(test_code)
                            status = test_code.get("status", "error")
                            reason = _generation_result_reason(test_code)
                            log_method = logger.info if status == "success" else logger.warning
                            log_method(
                                "test_code_generation result case=%s index=%s/%s status=%s "
                                "attempts=%s elapsed=%.1fs reason=%s",
                                test_code.get("test_case_id", f"TC_{i+1}"),
                                i + 1,
                                total_cases,
                                status,
                                retry_count,
                                elapsed_seconds,
                                "accepted by generation oracle" if status == "success" else reason,
                            )
                            if status == "success":
                                successful_generations += 1
                            break
                                
                        except Exception as retry_error:
                            error_msg = str(retry_error)
                            
                            # Gemini API özel hata handling
                            if is_gemini and ("503" in error_msg or "unavailable" in error_msg.lower()):
                                if retry_count < max_retries:
                                    wait_time = 2 ** retry_count  # Exponential backoff
                                    logger.warning(f"⏳ Gemini API unavailable, waiting {wait_time}s before retry {retry_count}/{max_retries}")
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    logger.error(f"❌ Gemini API still unavailable after {max_retries} retries")
                            elif is_gemini and ("timeout" in error_msg.lower() or "TimeoutError" in error_msg):
                                if retry_count < max_retries:
                                    logger.warning(f"⏰ Gemini API timeout, retry {retry_count}/{max_retries}")
                                    continue
                                else:
                                    logger.error(f"❌ Gemini API timeout after {max_retries} retries")
                            else:
                                logger.error(f"❌ Error in test generation: {error_msg}")
                            
                            # Persist the final retry failure with enough context.
                            if retry_count >= max_retries:
                                generated_tests.append({
                                    "test_case_id": _first_value(test_case, "TestCaseID", "test_case_id", default=f"TC_{i+1}"),
                                    "title": _first_value(test_case, "Title", "title", default="Unknown Test"),
                                    "status": "error",
                                    "error": error_msg,
                                    "code": None,
                                    "generation_attempts": retry_count,
                                    "failure_stage": "model_request",
                                })
                    
                    # Gemini API için rate limiting
                    if is_gemini and i < total_cases - 1:  # Son case değilse
                        await asyncio.sleep(0.5)  # 500ms bekle
                        
                except Exception as e:
                    logger.error(f"❌ Critical error generating test code for test case {i+1}: {str(e)}")
                    generated_tests.append({
                        "test_case_id": test_case.get("TestCaseID", f"TC_{i+1}"),
                        "title": test_case.get("Title", "Unknown Test"),
                        "status": "error",
                        "error": str(e),
                        "code": None
                    })
            
            status_counts = {
                status: len([item for item in generated_tests if item.get("status") == status])
                for status in ("success", "invalid", "unsupported", "error")
            }
            logger.info(
                "test_code_generation summary total=%s success=%s invalid=%s unsupported=%s error=%s",
                total_cases,
                status_counts["success"],
                status_counts["invalid"],
                status_counts["unsupported"],
                status_counts["error"],
            )
            for failed_test in [item for item in generated_tests if item.get("status") != "success"]:
                logger.warning(
                    "test_code_generation failure case=%s status=%s stage=%s reason=%s",
                    failed_test.get("test_case_id", "unknown"),
                    failed_test.get("status", "error"),
                    failed_test.get("failure_stage", "generation_oracle"),
                    _generation_result_reason(failed_test),
                )
            
            # 5. Sonuçları kaydet
            source_snapshot = [
                {
                    "filename": str(
                        getattr(item, "filename", None)
                        or getattr(item, "name", "source")
                    ),
                    "content": str(getattr(item, "content", "")),
                }
                for item in (source_files or [])
            ]
            result = {
                "success": True,
                "all_tests_generated": successful_generations == total_cases,
                "completion_rate": (
                    round((successful_generations / total_cases) * 100, 2)
                    if total_cases else 0.0
                ),
                "process_title": process_title,
                "environment_session_id": environment_session_id,
                "environment_info": environment_info,
                "total_test_cases": len(unique_test_cases),
                "generated_tests": generated_tests,
                "generated_count": len([t for t in generated_tests if t.get("status") == "success"]),
                "failed_count": len([t for t in generated_tests if t.get("status") == "error"]),
                "unsupported_count": len([t for t in generated_tests if t.get("status") == "unsupported"]),
                "invalid_count": len([t for t in generated_tests if t.get("status") == "invalid"]),
                "model_name": model_name,
                "custom_prompt": custom_prompt,
                "output_format": output_format,
                "capability_contract": (
                    capability_descriptor(capability_contract)
                    if capability_contract else None
                ),
                "project_structure": project_structure,
                "source_files": source_snapshot,
                "max_input_tokens": max_input_tokens,
                "timestamp": datetime.now().isoformat()
            }
            
            # Sonuçları veritabanına kaydet (both session_history and legacy collection)
            self._save_test_generation_results(result, session_id, environment_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in test code generation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_single_test_code(self, 
                                       test_case: Dict[str, Any], 
                                       code_analysis: Dict[str, Any], 
                                       environment_info: Dict[str, Any], 
                                       llm_client: LLMClient,
                                       test_number: int,
                                       custom_prompt: str = None,
                                       capability_contract: Dict[str, Any] = None,
                                       project_structure: Dict[str, Any] = None,
                                       max_input_tokens: int = 64000) -> Dict[str, Any]:
        """
        Tek bir test case için test kodu üretir
        """
        try:
            language = environment_info.get("language", "python")
            framework = environment_info.get("framework", "pytest")
            
            # Test case bilgilerini hazırla
            test_case_info = {
                "id": _first_value(
                    test_case, "TestCaseID", "test_case_id", default=f"TC_{test_number}"
                ),
                "title": _first_value(test_case, "Title", "title", default=""),
                "description": _first_value(test_case, "Description", "description", default=""),
                "objective": _first_value(test_case, "Objective", "objective", default=""),
                "steps": _first_value(
                    test_case, "TestSteps", "Steps", "steps", default=[]
                ),
                "expected_result": _first_value(
                    test_case, "ExpectedResult", "expected_result", default=""
                ),
                "target_symbols": _first_value(
                    test_case, "TargetSymbols", "target_symbols", default=[]
                ),
                "oracle_type": _first_value(
                    test_case, "OracleType", "oracle_type", default=""
                ),
                "expected_behavior": _first_value(
                    test_case, "ExpectedBehavior", "expected_behavior", default="pass"
                ),
            }
            
            # Framework'e özel template'ler
            framework_templates = {
                "pytest": {
                    "imports": "import pytest\nimport unittest.mock as mock",
                    "class_prefix": "class Test",
                    "method_prefix": "def test_",
                    "assertion_style": "assert"
                },
                "unittest": {
                    "imports": "import unittest\nfrom unittest import mock",
                    "class_prefix": "class Test",
                    "method_prefix": "def test_",
                    "assertion_style": "self.assertEqual"
                },
                "jest": {
                    "imports": "const request = require('supertest');\nconst { expect } = require('@jest/globals');",
                    "describe_prefix": "describe(",
                    "test_prefix": "test(",
                    "assertion_style": "expect"
                },
                "junit": {
                    "imports": "import org.junit.jupiter.api.Test;\nimport static org.junit.jupiter.api.Assertions.*;",
                    "class_prefix": "@Test\npublic class",
                    "method_prefix": "@Test\npublic void test",
                    "assertion_style": "assertEquals"
                }
            }
            
            template = framework_templates.get(framework, framework_templates["pytest"])
            
            # LLM prompt'u oluştur
            prompt = self._create_test_generation_prompt(
                test_case_info, 
                code_analysis, 
                environment_info, 
                template,
                custom_prompt,
                capability_contract,
                project_structure,
            )
            input_tokens = count_tokens(prompt)
            if input_tokens > max_input_tokens:
                raise ValueError(
                    f"Test {test_case_info['id']} input requires {input_tokens} tokens, "
                    f"exceeding the configured {max_input_tokens}-token budget. "
                    "Increase the budget up to 64000 or reduce the selected source/context."
                )
            
            # Model tipine göre timeout ayarları
            is_gemini = hasattr(llm_client, 'is_gemini') and llm_client.is_gemini
            
            # Büyük modeller için daha uzun timeout (20B+ parametreli modeller yavaş olabilir)
            is_large_model = any(size in llm_client.model_name.lower() for size in ['20b', '30b', '70b', '120b'])
            
            if is_gemini:
                timeout_seconds = 180  # Gemini için 3 dakika
            elif is_large_model:
                timeout_seconds = 120  # Büyük local modeller için 2 dakika
            else:
                # Local 3B/7B servers often need more than 60 seconds for a
                # grounded prompt. Scale by actual input size, with a hard cap.
                timeout_seconds = min(180, max(90, 60 + input_tokens // 250))

            logger.info(
                "test_code_generation model_request case=%s model=%s input_tokens=%s "
                "budget=%s timeout=%ss",
                test_case_info["id"],
                llm_client.model_name,
                input_tokens,
                max_input_tokens,
                timeout_seconds,
            )
            
            try:
                # LLM'den test kodu al - timeout ile
                response = await asyncio.wait_for(
                    llm_client.generate_response(
                        prompt,
                        temperature=0.2,
                        max_tokens=8192,
                        skip_chunking=True,
                    ),
                    timeout=timeout_seconds
                )
                
                if not response:
                    raise ValueError("No response from LLM")
                    
                logger.info(f"✅ Received response from {llm_client.model_name} (length: {len(response)})")
                
            except asyncio.TimeoutError:
                error_msg = f"Request to {llm_client.model_name} timed out after {timeout_seconds} seconds"
                logger.error(f"⏰ {error_msg}")
                raise TimeoutError(error_msg)
            except Exception as api_error:
                logger.error(f"🚨 API Error with {llm_client.model_name}: {str(api_error)}")
                raise
            
            # Test kodu response'unu temizle
            test_code = self._clean_test_code_response(response, language)

            if test_code.startswith("CAPABILITY_UNSUPPORTED:"):
                reason = test_code.split(":", 1)[1].strip() or "Test intent is not supported by the approved capability contract."
                return {
                    "test_case_id": test_case_info["id"],
                    "title": test_case_info["title"],
                    "description": test_case_info["description"],
                    "objective": test_case_info["objective"],
                    "framework": framework,
                    "language": language,
                    "code": None,
                    "status": "unsupported",
                    "execution_eligibility": "unsupported",
                    "eligibility_reason": reason,
                    "repair_attempted": False,
                    "input_tokens": input_tokens,
                    "input_token_budget": max_input_tokens,
                }

            image_tag = (
                capability_contract.get("meta", {})
                .get("pinned_sources", {})
                .get("image", {})
                .get("tag", "")
                if capability_contract else ""
            )
            allow_legacy_import = supports_legacy_sim_robot_goal(image_tag)
            def validate_candidate(candidate: str) -> Dict[str, Any]:
                report = evaluate_test_code(
                    candidate,
                    language,
                    allow_legacy_sim_robot_goal=allow_legacy_import,
                )
                capability_issues = (
                    validate_generated_code_against_capabilities(candidate, capability_contract)
                    if capability_contract else []
                )
                project_issues = validate_code_against_project_structure(candidate, project_structure)
                for check_name, issues in (
                    ("project_ast_contract", project_issues),
                    ("robot_capability_contract", capability_issues),
                ):
                    if not issues:
                        continue
                    report["issues"].extend(issues)
                    report["checks"].append({
                        "name": check_name,
                        "passed": False,
                        "details": " ".join(issues),
                    })
                    report["passed"] = False
                    report["verdict"] = "fail"
                report["issues"] = list(dict.fromkeys(report["issues"]))
                return report

            oracle_report = validate_candidate(test_code)
            repair_attempts = 0
            max_repair_attempts = 3
            capability_repair_rules = """
Do not define, copy, embed, mock, or replace a controller or any other system-under-test class.
Use only imports and APIs explicitly declared by the approved capability contract.
Preserve the original observable test intent. Do not substitute an unrelated robot action merely to make the code executable.
If that intent cannot be tested through the declared capability API, return exactly:
CAPABILITY_UNSUPPORTED: <concrete reason>
""".strip() if capability_contract else """
Embed only genuinely required test helpers in the same file. Do not copy the system under test.
""".strip()

            while not oracle_report["passed"] and repair_attempts < max_repair_attempts:
                repair_attempts += 1
                logger.warning(
                    "test_code_generation oracle_repair case=%s attempt=%s/%s issues=%s",
                    test_case_info["id"],
                    repair_attempts,
                    max_repair_attempts,
                    " | ".join(oracle_report["issues"]),
                )
                repair_prompt = f"""You are a deterministic Python test-code repair engine.
The previous generated code failed the execution oracle on repair attempt
{repair_attempts} of {max_repair_attempts}.

Test case ID: {test_case_info['id']}
Objective: {test_case_info['objective']}
Target symbols: {json.dumps(test_case_info.get('target_symbols', []), ensure_ascii=False)}

Oracle findings:
{chr(10).join(f'- {issue}' for issue in oracle_report['issues'])}

Rewrite the complete test code and fix every finding. Preserve the test intent.
- Never emit `pass`, ellipsis, TODO, FIXME, or NotImplementedError. For a no-op
  fake method, write `return None`.
- Prefer unittest.mock.MagicMock/Mock over handwritten ROS or MoveIt stub classes.
- Do not call executor.spin(), create_rate(...).sleep(), or while rclpy.ok().
- Avoid rclpy.init() when mocking is sufficient. If initialization is essential,
  put it in a try block and call rclpy.shutdown() in that try statement's finally.
- Every imported/referenced name must be bound in this single file.
- Keep at least one assertion tied to an observable return value, state change,
  exception, or mock call; never use unconditional `assert True`.

{capability_repair_rules}

Return only the corrected executable code or CAPABILITY_UNSUPPORTED.

## PREVIOUS INVALID CODE
{test_code}
""".strip()
                repair_tokens = count_tokens(repair_prompt)
                if repair_tokens > max_input_tokens:
                    raise ValueError(
                        f"Oracle repair input requires {repair_tokens} tokens, exceeding "
                        f"the configured {max_input_tokens}-token budget."
                    )
                repaired_response = await asyncio.wait_for(
                    llm_client.generate_response(
                        repair_prompt,
                        temperature=0.1,
                        max_tokens=8192,
                        skip_chunking=True,
                    ),
                    timeout=timeout_seconds,
                )
                test_code = self._clean_test_code_response(repaired_response, language)
                if test_code.startswith("CAPABILITY_UNSUPPORTED:"):
                    reason = test_code.split(":", 1)[1].strip() or "Test intent is not supported by the approved capability contract."
                    return {
                        "test_case_id": test_case_info["id"],
                        "title": test_case_info["title"],
                        "description": test_case_info["description"],
                        "objective": test_case_info["objective"],
                        "framework": framework,
                        "language": language,
                        "code": None,
                        "status": "unsupported",
                        "execution_eligibility": "unsupported",
                        "eligibility_reason": reason,
                        "repair_attempted": True,
                        "repair_attempts": repair_attempts,
                        "input_tokens": input_tokens,
                        "input_token_budget": max_input_tokens,
                    }
                oracle_report = validate_candidate(test_code)

            if not oracle_report["passed"]:
                reason = (
                    f"Generated code failed the execution oracle after {repair_attempts} automatic repair attempts: "
                    + " ".join(oracle_report["issues"])
                )
                return {
                    "test_case_id": test_case_info["id"],
                    "title": test_case_info["title"],
                    "description": test_case_info["description"],
                    "objective": test_case_info["objective"],
                    "framework": framework,
                    "language": language,
                    "code": test_code,
                    "status": "invalid",
                    "execution_eligibility": "invalid",
                    "eligibility_reason": reason,
                    "error": reason,
                    "failure_stage": "generation_oracle",
                    "repair_attempted": repair_attempts > 0,
                    "repair_attempts": repair_attempts,
                    "oracle": oracle_report,
                    "input_tokens": input_tokens,
                    "input_token_budget": max_input_tokens,
                }
            
            return {
                "test_case_id": test_case_info["id"],
                "title": test_case_info["title"],
                "description": test_case_info["description"],
                "objective": test_case_info["objective"],
                "framework": framework,
                "language": language,
                "code": test_code,
                "status": "success",
                "execution_eligibility": "eligible",
                "eligibility_reason": None,
                "repair_attempted": repair_attempts > 0,
                "repair_attempts": repair_attempts,
                "filename": self._generate_filename(test_case_info["title"], language, test_number),
                "oracle": oracle_report,
                "input_tokens": input_tokens,
                "input_token_budget": max_input_tokens,
            }
            
        except Exception as e:
            logger.error(
                "test_code_generation exception case=%s stage=single_test_generation "
                "exception_type=%s reason=%s",
                _first_value(test_case, "TestCaseID", "test_case_id", default=f"TC_{test_number}"),
                type(e).__name__,
                str(e),
            )
            logger.debug("test_code_generation exception traceback", exc_info=True)
            return {
                "test_case_id": _first_value(test_case, "TestCaseID", "test_case_id", default=f"TC_{test_number}"),
                "title": _first_value(test_case, "Title", "title", default="Unknown Test"),
                "status": "error",
                "error": str(e),
                "failure_stage": "single_test_generation",
                "code": None,
            }
    
    def _create_test_generation_prompt(self, 
                                     test_case_info: Dict[str, Any], 
                                     code_analysis: Dict[str, Any], 
                                     environment_info: Dict[str, Any], 
                                     template: Dict[str, Any],
                                     custom_prompt: str = None,
                                     capability_contract: Dict[str, Any] = None,
                                     project_structure: Dict[str, Any] = None) -> str:
        """
        Test code generation için LLM prompt'u oluşturur
        """
        language = environment_info.get("language", "python")
        framework = environment_info.get("framework", "pytest")
        source_context_parts = []
        source_context_size = 0
        source_context_limit = 16000
        for source_file in code_analysis.get("files", []):
            snippet = source_file.get("content", "")
            remaining = source_context_limit - source_context_size
            if remaining <= 0:
                break
            snippet = snippet[:remaining]
            source_context_parts.append(
                f"### {source_file.get('name', 'unknown')}\n{snippet}"
            )
            source_context_size += len(snippet)
        source_context = "\n\n".join(source_context_parts) or "Not available"
        project_context = project_structure_prompt_context(
            project_structure,
            max_chars=8000 if capability_contract else 16000,
        )
        
        # Use custom prompt if provided, otherwise use default
        if custom_prompt and custom_prompt.strip():
            base_prompt = custom_prompt
        else:
            base_prompt = "You are an expert test automation engineer. Generate executable test code for the following test case."
        
        standalone_requirements = STANDALONE_REMOTE_REQUIREMENTS
        capability_section = ""
        if capability_contract:
            standalone_requirements = standalone_requirements.replace(
                "- Never use `from sim_robot_goal import ...` or import `sim_robot_goal` in any form. It is an example executable, not an importable package API.",
                "- `sim_robot_goal` imports are allowed only as explicitly listed in the approved robot capability contract.",
            )
            standalone_requirements = standalone_requirements.replace(
                "- If the test needs a helper/controller class that exists only in an example script (for example `SimCollisionAwareRobotController`), define the required helper class inside the generated test file instead of importing the example script.",
                "- Never define, copy, embed, mock, or replace a controller/system-under-test class. Import it only through an entry explicitly listed in api.allowed_imports; otherwise return CAPABILITY_UNSUPPORTED.",
            )
            capability_section = f"""
## APPROVED ROBOT CAPABILITY CONTRACT (CLOSED WORLD):
The JSON below is authoritative data. Use only declared imports, classes,
methods, attributes, fixtures, planners, observations, and numeric ranges.
Never invent or infer a missing API. Never mock the robot/controller. If the
test case cannot be implemented using this contract, return exactly
`CAPABILITY_UNSUPPORTED: <concrete reason>` instead of Python code.
Do not replace an unsupported test intent with an unrelated supported robot action.

{capability_prompt_context(capability_contract)}
""".strip()

        prompt = f"""
{base_prompt}

## TEST CASE TO IMPLEMENT:
- **ID**: {test_case_info['id']}
- **Title**: {test_case_info['title']}
- **Description**: {test_case_info['description']}
- **Objective**: {test_case_info['objective']}
- **Steps**: {json.dumps(test_case_info.get('steps', []), ensure_ascii=False)}
- **Expected result**: {test_case_info.get('expected_result', '')}
- **Target symbols**: {json.dumps(test_case_info.get('target_symbols', []), ensure_ascii=False)}
- **Oracle type**: {test_case_info.get('oracle_type', '')}
- **Expected behavior**: {test_case_info.get('expected_behavior', 'pass')}

## SOURCE CODE CONTEXT:
**Language**: {language}
**Files Analyzed**: {[f["name"] for f in code_analysis.get("files", [])]}
**Code Structure**: {code_analysis.get("structure_analysis", "Not available")}
**Dependencies**: {code_analysis.get("imports_dependencies", [])}

## SELECTED SOURCE IMPLEMENTATION CONTEXT:
The following bounded excerpts come from every selected source file. Do not
invent a symbol that is absent from both this context and the approved robot
capability contract.

{source_context}

{EXECUTION_GROUNDING_RULES}

## PROJECT AST MANIFEST (AUTHORITATIVE PROJECT SYMBOLS):
{project_context}

## TEST FRAMEWORK & ENVIRONMENT:
**Framework**: {framework}
**Language**: {language}
**Required Imports**: {template.get("imports", "")}

{capability_section}

## REQUIREMENTS:
1. Generate complete, executable test code using {framework}
2. Use proper {framework} conventions and syntax
3. Include necessary imports and setup
4. Make the test specific to the test case objective
5. Add meaningful assertions
6. Include docstring explaining the test purpose
7. Make it ready to run without modifications

## ROS/MOVEIT UNIT-TEST PATTERN (MANDATORY FOR THIS SOURCE):
- Prefer MagicMock/Mock and monkeypatch for ROS nodes, executors, MoveIt clients,
  clocks, publishers, and futures; do not recreate whole external frameworks.
- Never use a `pass` body in a fake/stub; use `return None` or a concrete value.
- Never start executor.spin(), create_rate(...).sleep(), or a while-rclpy-ok loop.
- Avoid rclpy.init() for mocked unit tests. If it is unavoidable, pair it with
  rclpy.shutdown() inside the same try/finally statement.
- Assert an observable value, state transition, exception, or mock call.

{standalone_requirements if language.lower() in {"python", "py", "python3"} else ""}

{ORACLE_PROMPT_REQUIREMENTS}

## OUTPUT FORMAT:
Return ONLY the executable test code, no explanations or markdown formatting.
"""
        
        return prompt.strip()
    
    def _clean_test_code_response(self, response: str, language: str) -> str:
        """
        LLM response'undan temiz test kodu çıkarır
        """
        try:
            # Markdown code blocks'ları temizle
            cleaned = response.strip()
            
            # ```python veya ``` ile başlıyorsa temizle
            if cleaned.startswith(f"```{language}"):
                cleaned = cleaned[len(f"```{language}"):].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:].strip()
            
            # Son ``` varsa temizle
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning test code response: {str(e)}")
            return response
    
    def _generate_filename(self, title: str, language: str, test_number: int) -> str:
        """
        Test dosyası için uygun filename oluşturur
        """
        try:
            # Title'ı temizle ve filename uygun hale getir
            import re
            clean_title = re.sub(r'[^\w\s-]', '', title.lower())
            clean_title = re.sub(r'[-\s]+', '_', clean_title)
            
            # Dil uzantılarına göre filename oluştur
            extensions = {
                "python": ".py",
                "javascript": ".js", 
                "java": ".java",
                "csharp": ".cs"
            }
            
            extension = extensions.get(language, ".py")
            return f"test_{clean_title}_{test_number:02d}{extension}"
            
        except Exception as e:
            logger.error(f"Error generating filename: {str(e)}")
            return f"test_case_{test_number:02d}.py"
    
    def _save_test_generation_results(self, results: Dict[str, Any], session_id: str = None, environment_name: str = None):
        """
        Test generation sonuçlarını veritabanına processes.test_code_generation altına kaydet
        Cleaned structure - removes redundancies and unifies field names
        """
        try:
            logger.info(f"🔍 Debug: Attempting to save session with session_id: {session_id}")
            logger.info(f"🔍 Debug: Environment name: {environment_name}")
            logger.info(f"🔍 Debug: Results keys: {list(results.keys())}")
            
            # Session_id varsa session_history'ye kaydet
            if session_id:
                logger.info(f"📝 Creating clean session document for session_id: {session_id}")
                
                # Create clean, unified structure
                clean_structure = {
                    "status": "completed" if results.get("success") else "failed",
                    "timestamp": datetime.now().isoformat(),
                    "process_name": environment_name,  # Required field from frontend
                    "code_generation_process_name": environment_name,  # Required field for Test Execution
                    "model_name": results.get("model_name", "llama3.2:3b"),  # Unified field name
                    "input": {
                        "process_title": results.get("process_title"),
                        "model_name": results.get("model_name", "llama3.2:3b"),  # Unified field name
                        "environment_session_id": results.get("environment_session_id"),
                        "output_format": results.get("output_format", "JSON"),  # Add missing UI field
                        "total_test_cases": results.get("total_test_cases", 0),
                        "source_files": results.get("source_files", []),
                        "capability_contract": results.get("capability_contract"),
                        "max_input_tokens": results.get("max_input_tokens", 64000),
                    },
                    "output": {
                        "success": results.get("success", False),
                        "all_tests_generated": results.get("all_tests_generated", False),
                        "completion_rate": results.get("completion_rate", 0.0),
                        "generated_tests": results.get("generated_tests", []),
                        "generated_count": results.get("generated_count", 0),
                        "failed_count": results.get("failed_count", 0),
                        "unsupported_count": results.get("unsupported_count", 0),
                        "invalid_count": results.get("invalid_count", 0),
                        "environment_info": results.get("environment_info", {}),  # Keep only one copy
                        "data": results  # Backward compatibility
                    }
                }
                
                # Add custom_prompt only if provided
                if results.get("custom_prompt"):
                    clean_structure["input"]["custom_prompt"] = results.get("custom_prompt")
                
                # Use dot notation to safely update only test_code_generation process
                update_query = {
                    "$set": {
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "processes.test_code_generation": clean_structure
                    }
                }
                
                result = self.session_collection.update_one(
                    {"session_id": session_id},
                    update_query,
                    upsert=True
                )
                
                logger.info(f"✅ Clean structure saved - matched: {result.matched_count}, modified: {result.modified_count}, upserted: {result.upserted_id}")
                logger.info(f"Test generation results saved to session_history for session: {session_id}")
                
                # Verify save by querying back
                saved_doc = self.session_collection.find_one({"session_id": session_id})
                if saved_doc:
                    logger.info(f"✅ Verification: Clean document found in session_history with _id: {saved_doc.get('_id')}")
                else:
                    logger.error(f"❌ Verification failed: Document not found in session_history for session: {session_id}")
            else:
                logger.warning(f"⚠️ session_id is None or empty - skipping session_history save")
                logger.warning(f"⚠️ This means the results will not be saved to session_history collection")
            
            # Backward compatibility: ayrı collection'a da kaydet
            test_generation_collection = self.db["test_code_generation_results"]
            
            document = {
                **results,
                "session_id": session_id,
                "environment_name": environment_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Upsert: process_title'a göre güncelle veya yeni oluştur
            test_generation_collection.update_one(
                {"process_title": results["process_title"]},
                {"$set": document},
                upsert=True
            )
            
            logger.info(f"Test generation results also saved to test_code_generation_results collection")
            
        except Exception as e:
            logger.error(f"Error saving test generation results: {str(e)}")

    def get_available_process_titles(self) -> List[Dict[str, Any]]:
        """
        Session history'den test case optimization process name'leri getirir
        Her process için unique test case sayısını da içerir
        Path: session_history->processes->test_case_optimization->process_name
        """
        try:
            # Session history'den process name ve unique test case sayılarını al
            pipeline = [
                {
                    "$match": {
                        "processes.test_case_optimization": {"$exists": True}
                    }
                },
                {
                    "$project": {
                        "process_name": "$processes.test_case_optimization.process_name",
                        "unique_test_cases_count": {
                            "$size": {
                                "$ifNull": ["$processes.test_case_optimization.output.unique_test_cases", []]
                            }
                        }
                    }
                },
                {
                    "$sort": {"process_name": 1}
                }
            ]
            
            results = list(self.session_collection.aggregate(pipeline))
            
            # Process name ve count bilgilerini dict olarak döndür
            process_info = [
                {
                    "process_name": r["process_name"],
                    "test_case_count": r["unique_test_cases_count"]
                }
                for r in results if r.get("process_name")
            ]
            
            logger.info(f"Found {len(process_info)} available process names with test case counts from session_history")
            return process_info
            
        except Exception as e:
            logger.error(f"Error getting available process titles: {str(e)}")
            return []
    
    def get_generated_tests_by_process_name(self, process_name: str) -> List[Dict[str, Any]]:
        """
        Get generated tests for a specific process name from session history
        Path: session_history->processes->test_code_generation->generated_tests
        
        Args:
            process_name: The process name to filter by (process_name field)
            
        Returns:
            List of generated tests with test_id, test_case_name, status, test_code
        """
        try:
            logger.info(f"Fetching generated tests for process: {process_name}")
            
            # Query session history for test_code_generation with matching process_name
            pipeline = [
                {
                    "$match": {
                        "processes.test_code_generation": {"$exists": True},
                        "processes.test_code_generation.process_name": process_name
                    }
                },
                {
                    "$project": {
                        "session_id": 1,
                        "timestamp": "$processes.test_code_generation.timestamp",
                        "generated_tests": "$processes.test_code_generation.output.generated_tests",
                        "process_name": "$processes.test_code_generation.process_name"
                    }
                },
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$limit": 1  # Get the most recent session
                }
            ]
            
            results = list(self.session_collection.aggregate(pipeline))
            
            if not results:
                logger.warning(f"No generated tests found for process: {process_name}")
                return []
            
            # Extract generated tests from the most recent session
            latest_session = results[0]
            generated_tests = latest_session.get("generated_tests", [])
            
            # Format the tests for the response
            formatted_tests = []
            for test in generated_tests:
                formatted_test = {
                    "unique_id": test.get("unique_id", ""),
                    "test_id": test.get("test_case_id", ""),
                    "test_case_name": test.get("title", ""),
                    "status": test.get("status", "unknown"),
                    "test_code": test.get("code", ""),
                    "error": test.get("error", None),
                    "description": test.get("description", ""),
                    "filename": test.get("filename", "")
                }
                formatted_tests.append(formatted_test)
            
            logger.info(f"Found {len(formatted_tests)} generated tests for process: {process_name}")
            return formatted_tests
            
        except Exception as e:
            logger.error(f"Error getting generated tests for process {process_name}: {str(e)}")
            return []
    
    def get_process_names_with_generated_tests(self) -> List[str]:
        """
        Get list of unique process names that have generated tests
        Path: session_history->processes->test_code_generation->process_name
        
        Returns:
            List of unique process names (process_name values)
        """
        try:
            logger.info("Fetching process names with generated tests")
            
            # Query for distinct process_name values where test_code_generation exists
            pipeline = [
                {
                    "$match": {
                        "processes.test_code_generation": {"$exists": True},
                        "processes.test_code_generation.status": "completed"
                    }
                },
                {
                    "$group": {
                        "_id": "$processes.test_code_generation.process_name"
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            results = list(self.session_collection.aggregate(pipeline))
            process_names = [r["_id"] for r in results if r.get("_id")]
            
            logger.info(f"Found {len(process_names)} process names with generated tests")
            return process_names
            
        except Exception as e:
            logger.error(f"Error getting process names with generated tests: {str(e)}")
            return []
