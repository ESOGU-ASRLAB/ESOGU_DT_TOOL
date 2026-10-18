from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from stlc.test_scenario_generation import generate_prompt, run_step
from services.prompt_generation_service import PromptGenerationService
from typing import Dict, List, Optional
from core.database import get_database
from datetime import datetime
import json
import logging
from datetime import datetime
from utils.model_client import LLMClient
from services.project_structure_service import (
    EXECUTION_GROUNDING_RULES,
    ProjectStructureError,
    build_project_structure,
    is_project_structure_file,
    parse_project_structure,
    project_structure_prompt_context,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["test-scenario-generation"]
)


async def _project_structure_from_uploads(
    files: Optional[List[UploadFile]],
    project_ast_file: Optional[UploadFile] = None,
    relative_paths: Optional[List[str]] = None,
):
    if project_ast_file is not None:
        return parse_project_structure(
            await project_ast_file.read(),
            project_ast_file.filename or "project_ast.json",
        )
    source_items = []
    for index, upload in enumerate(files or []):
        raw = await upload.read()
        await upload.seek(0)
        source_items.append({
            "name": (
                relative_paths[index]
                if relative_paths and index < len(relative_paths)
                else upload.filename or "unknown"
            ),
            "content": raw.decode("utf-8", errors="replace"),
        })
    return build_project_structure(source_items)


@router.post("/project-structure")
async def create_project_structure(
    files: List[UploadFile] = File(...),
    paths: List[str] = Form(default=[]),
):
    """Build one compact project manifest from a selected source folder."""
    try:
        manifest = await _project_structure_from_uploads(files, relative_paths=paths)
        if not manifest.get("project_files"):
            raise HTTPException(status_code=400, detail="No supported source files were supplied")
        return {"status": "success", "project_structure": manifest}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to build project structure: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/model-context-length/{model_key}")
async def get_model_context_length(model_key: str):
    """
    Verilen model key için LM Studio'dan gerçek context length bilgisini döndürür.
    Frontend bu endpoint'i model seçildiğinde çağırarak dinamik token sınırını gösterebilir.
    """
    try:
        client = LLMClient()
        actual_model = client.get_model_identifier(model_key)
        context_length = await client.get_model_context_length(actual_model)
        # safe_input_limit: context_length - max_output_tokens (4000) - overhead (500)
        safe_input_limit = max(context_length - 4000 - 500, 1000)
        return {
            "model_key": model_key,
            "model_identifier": actual_model,
            "context_length": context_length,
            "safe_input_token_limit": safe_input_limit,
        }
    except Exception as e:
        logger.error(f"[ERROR] get_model_context_length failed for '{model_key}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-prompt")
async def generate_test_scenario_prompt(request: Request):
    """
    Test senaryosu için custom prompt oluşturur (LLM ile).
    JSON body ile fileContents array'ini destekler.
    """
    try:
        data = await request.json()
        
        # Debug logging
        logger.info(f"[DEBUG] Received request data keys: {list(data.keys())}")
        if 'fileContents' in data:
            file_contents = data['fileContents']
            logger.info(f"[DEBUG] fileContents type: {type(file_contents)}, length: {len(file_contents) if isinstance(file_contents, list) else 'not a list'}")
        
        result = await generate_prompt(data)
        
        # Hata kontrolü - result'ın status'unu kontrol et
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))
        
        # Final prompt'u ve session_id'yi döndür (varsa)
        return {
            "generated_custom_prompt": result.get("generated_custom_prompt", ""),
            "session_id": result.get("session_id", ""),
            "project_structure": result.get("project_structure", {}),
            "status": "success"
        }
    except HTTPException:
        raise  # HTTPException'ları yeniden fırlat
    except Exception as e:
        logger.error(f"[ERROR] Exception in generate_test_scenario_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run")
async def run_test_scenario_generation(
    files: List[UploadFile] = File(default=None),
    model: str = Form(None),
    final_prompt: str = Form(...),
    test_category: str = Form(None),
    test_type: str = Form(None),
    session_id: str = Form(None),
    process_title: str = Form(None),
    api_key: Optional[str] = Form(None),
    project_ast_file: Optional[UploadFile] = File(None),
):
    """
    Test senaryosu üretim işlemini çalıştırır.
    Custom prompt + seçilen dosyalar kullanarak test senaryoları üretir.
    """
    try:
        logger.info(f"[DEBUG] run_test_scenario_generation called with:")
        logger.info(f"[DEBUG] - files count: {len(files) if files else 0}")
        logger.info(f"[DEBUG] - model: {model}")
        logger.info(f"[DEBUG] - final_prompt length: {len(final_prompt) if final_prompt else 0}")
        logger.info(f"[DEBUG] - test_category: {test_category}")
        logger.info(f"[DEBUG] - test_type: {test_type}")
        logger.info(f"[DEBUG] - process_title: {process_title}")

        if not final_prompt:
            raise HTTPException(status_code=400, detail="Final prompt is required")
            
        if not process_title or not process_title.strip():
            raise HTTPException(status_code=400, detail="Process title is required")

        try:
            project_structure = await _project_structure_from_uploads(files, project_ast_file)
        except ProjectStructureError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        data = {
            "files": files if files else [],
            "model": model or "llama3.2:3b",  # Default model
            "final_prompt": final_prompt,
            "test_category": test_category,
            "test_type": test_type,
            "session_id": session_id,
            "process_title": process_title,
            "api_key": api_key,
            "project_structure": project_structure,
        }
        
        logger.info(f"[DEBUG] Calling run_step with data")
        result = await run_step(data)
        
        logger.info(f"[DEBUG] run_step result status: {result.get('status')}")
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))
        
        return result
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"[DEBUG] Error in run_test_scenario_generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def read_test_scenarios():
    try:
        db = await get_database()
        # Add your test scenario logic here
        return {"message": "Test scenarios endpoint"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-type/{test_type}")
async def get_test_type_details(test_type: str):
    """
    Fetch complete test type details including prompt and scoring elements.
    """
    try:
        print(f"Fetching details for test type: {test_type}")
        db = await get_database()
        test_collection = db["test_scenario_generation_prompt"]
        
        # Find document matching the test type
        doc = await test_collection.find_one({"test_name": test_type})
        print(f"Found document: {doc}")
        
        if not doc:
            print(f"No document found for test type: {test_type}")
            raise HTTPException(status_code=404, detail=f"No details found for test type: {test_type}")
            
        response_data = {
            "test_prompt": doc.get("test_prompt", ""),
            "test_scoring_elements_and_prompts": doc.get("test_scoring_elements_and_prompts", {}),
            "test_instruction_elements_and_prompts": doc.get("test_instruction_elements_and_prompts", {})
        }
        print(f"Returning response: {response_data}")
        return response_data
    except Exception as e:
        print(f"Error in get_test_type_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-types")
async def list_available_test_types():
    """
    Veritabanında bulunan test tiplerini listeler.
    """
    try:
        db = await get_database()
        test_collection = db["test_scenario_generation_prompt"]
        
        # Tüm test tiplerini listele
        cursor = test_collection.find({}, {"test_name": 1, "_id": 0})
        test_types = []
        async for doc in cursor:
            test_types.append(doc.get("test_name"))
        
        return {
            "test_types": test_types,
            "count": len(test_types)
        }
    except Exception as e:
        print(f"Error in list_available_test_types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-test-scenarios")
async def generate_test_scenarios(request: Request):
    """
    Üretilen prompt ile seçili dosyaları kullanarak test senaryoları oluşturur.
    JSON body: {
        "finalPrompt": "string",
        "selectedFiles": ["file1.txt", "file2.txt"],
        "model": "gpt-4",
        "test_type": "functional",
        "test_category": "positive"
    }
    """
    try:
        data = await request.json()
        logger.info(f"[DEBUG] Generate test scenarios request: {list(data.keys())}")
        
        final_prompt = data.get("finalPrompt", "")
        selected_files = data.get("selectedFiles", [])
        model = data.get("model", "gpt-4")
        test_type = data.get("test_type", "")
        test_category = data.get("test_category", "")
        api_key = data.get("api_key")  # API key extraction
        
        if not final_prompt:
            raise HTTPException(status_code=400, detail="Final prompt is required")
        
        if not selected_files:
            raise HTTPException(status_code=400, detail="At least one file must be selected")
        
        # Dosya içeriklerini oku
        file_contents = ""
        for file_path in selected_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    file_contents += f"\n\n=== FILE: {file_path} ===\n{content}\n"
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {e}")
                continue
        
        if not file_contents.strip():
            raise HTTPException(status_code=400, detail="Could not read any selected files")
        
        # LLM client'ı oluştur
        from utils.model_client import LLMClient
        llm_client = LLMClient(api_key=api_key, use_case='test_scenario_generation')
        
        # Test senaryosu üretme prompt'u oluştur
        test_scenario_prompt = f"""{final_prompt}

## FILE CONTENTS TO ANALYZE:
{file_contents}

## OUTPUT REQUIREMENTS:
Generate comprehensive test scenarios based on the above prompt and file contents. Return ONLY a valid JSON object with the following structure:

{{
  "TestScenarios": [
    {{
      "ScenarioID": "TS_001",
      "Title": "Clear and descriptive test scenario title",
      "Description": "Detailed description of what this test scenario covers",
      "Objective": "What this test aims to verify or validate",
      "Category": "Functional/Non-Functional/Security/Performance/etc.",
      "Comments": "Additional notes, assumptions, or considerations"
    }}
  ],
  "Summary": {{
    "TotalScenarios": 0,
    "Categories": {{}},
    "Coverage": "Brief description of what aspects are covered by these scenarios"
  }}
}}

Generate between 5-10 comprehensive test scenarios that cover different aspects of the provided files and requirements. Ensure each scenario is practical, executable, and directly related to the file contents."""

        logger.info(f"Sending test scenario generation request to LLM model: {model}")
        
        # LLM'e test senaryoları üretmesi için istek gönder
        response = await llm_client.generate_response(
            test_scenario_prompt,
            temperature=0.3,
            max_tokens=4000
        )
        
        if not response:
            raise HTTPException(status_code=500, detail="No response from LLM")
        
        logger.info(f"Received LLM response length: {len(response)}")
        
        # JSON response'u parse et
        try:
            # JSON pattern'i bul
            import re
            json_pattern = r'\{[\s\S]*?"TestScenarios"[\s\S]*?\}(?:\s*\})?'
            json_match = re.search(json_pattern, response)
            
            if json_match:
                json_str = json_match.group(0)
                # Ensure proper JSON closure
                if not json_str.rstrip().endswith('}'):
                    json_str += '}'
                
                test_scenarios = json.loads(json_str)
                
                # Validate structure
                if "TestScenarios" not in test_scenarios:
                    raise ValueError("TestScenarios key not found in response")
                
                scenarios = test_scenarios["TestScenarios"]
                if not isinstance(scenarios, list):
                    raise ValueError("TestScenarios must be a list")
                
                # Add summary if not present
                if "Summary" not in test_scenarios:
                    categories = {}
                    for scenario in scenarios:
                        cat = scenario.get("Category", "Unknown")
                        categories[cat] = categories.get(cat, 0) + 1
                    
                    test_scenarios["Summary"] = {
                        "TotalScenarios": len(scenarios),
                        "Categories": categories,
                        "Coverage": f"Generated {len(scenarios)} test scenarios covering various aspects of the provided files"
                    }
                
                logger.info(f"Successfully generated {len(scenarios)} test scenarios")
                
                return {
                    "status": "success",
                    "test_scenarios": test_scenarios,
                    "metadata": {
                        "model_used": model,
                        "files_processed": len(selected_files),
                        "total_scenarios": len(scenarios),
                        "test_type": test_type,
                        "test_category": test_category
                    }
                }
                
            else:
                # Try to parse the whole response as JSON
                test_scenarios = json.loads(response)
                if "TestScenarios" in test_scenarios:
                    return {
                        "status": "success",
                        "test_scenarios": test_scenarios,
                        "metadata": {
                            "model_used": model,
                            "files_processed": len(selected_files),
                            "total_scenarios": len(test_scenarios.get("TestScenarios", [])),
                            "test_type": test_type,
                            "test_category": test_category
                        }
                    }
                else:
                    raise ValueError("Invalid response format from LLM")
                    
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response preview: {response[:500]}")
            raise HTTPException(status_code=500, detail=f"Failed to parse LLM response as JSON: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating test scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-prompt-file-aware")
async def generate_file_aware_prompt(
    files: List[UploadFile] = File(...),
    test_type: Optional[str] = Form(None),
    test_category: Optional[str] = Form(None),
    base_prompt: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """
    Dosya içeriklerine dayalı custom prompt oluşturur.
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded.")
        
        prompt_service = PromptGenerationService()
        result = await prompt_service.generate_file_aware_prompt(
            files=files,
            test_type=test_type,
            test_category=test_category,
            base_prompt=base_prompt,
            model_key=model,
            session_id=session_id
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Prompt generation failed"))
        
        return {
            "status": "success",
            "generated_custom_prompt": result.get("generated_custom_prompt", ""),
            "files_analyzed": result.get("files_analyzed", {}),
            "file_analysis_summary": result.get("file_analysis_summary", ""),
            "session_id": result.get("session_id", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/process-titles")
async def get_test_scenario_process_titles():
    """
    Test Scenario Generation işlemlerinin process_title'larını listeler.
    Sadece process_title'ı olan ve boş olmayan kayıtları döndürür.
    """
    try:
        logger.info("[DEBUG] get_test_scenario_process_titles endpoint called")
        
        db = await get_database()
        collection = db["session_history"]
        
        logger.info("[DEBUG] Database connection successful")
        
        # Test scenario generation process'leri olan ve process_title'ı boş olmayan kayıtları bul
        pipeline = [
            {
                "$match": {
                    "processes.test_scenario_generation": {"$exists": True},
                    "processes.test_scenario_generation.process_title": {
                        "$exists": True, 
                        "$ne": "", 
                        "$ne": None
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,  # _id'yi exclude et
                    "session_id": 1,
                    "created_at": {"$dateToString": {"format": "%Y-%m-%d %H:%M:%S", "date": "$created_at"}},  # datetime'ı string'e çevir
                    "process_title": "$processes.test_scenario_generation.process_title",
                    "test_type": "$processes.test_scenario_generation.output.metadata.test_type",
                    "test_category": "$processes.test_scenario_generation.output.metadata.test_category"
                }
            },
            {
                "$sort": {"created_at": -1}  # En yeni kayıtlar önce
            }
        ]
        
        logger.info(f"[DEBUG] Executing aggregation pipeline: {pipeline}")
        
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        logger.info(f"[DEBUG] Found {len(results)} test scenario processes with process_title")
        logger.info(f"[DEBUG] Results: {results}")
        
        return {
            "status": "success",
            "process_titles": results
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Error getting test scenario process titles: {str(e)}")
        logger.error(f"[ERROR] Exception type: {type(e)}")
        import traceback
        logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/process-data/{session_id}")
async def get_test_scenario_process_data(session_id: str):
    """
    Belirli bir session_id'ye ait test scenario generation verilerini getirir.
    test_type, test_category ve test_scenarios dizisini döndürür.
    """
    try:
        db = await get_database()
        collection = db["session_history"]
        
        # Belirtilen session_id'ye ait test scenario generation verisini bul
        document = await collection.find_one(
            {
                "session_id": session_id,
                "processes.test_scenario_generation": {"$exists": True}
            }
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Test scenario data not found for this session")
        
        test_scenario_data = document.get("processes", {}).get("test_scenario_generation", {})
        output_data = test_scenario_data.get("output", {})
        
        # Test scenarios dizisini al
        test_scenarios = []
        test_type = ""
        test_category = ""
        
        if "test_scenarios" in output_data:
            test_scenarios = output_data["test_scenarios"]
        
        # Metadata'dan test_type ve test_category'yi al
        metadata = output_data.get("metadata", {})
        test_type = metadata.get("test_type", "")
        test_category = metadata.get("test_category", "")
        
        result = {
            "session_id": session_id,
            "process_title": test_scenario_data.get("process_title", ""),
            "test_type": test_type,
            "test_category": test_category,
            "test_scenarios": test_scenarios,
            "created_at": document.get("created_at")
        }
        
        logger.info(f"[DEBUG] Retrieved test scenario data for session {session_id}")
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error getting test scenario process data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-connection")
async def test_database_connection():
    """
    Test endpoint to check MongoDB connection
    """
    try:
        db = await get_database()
        collection = db["session_history"]
        
        # Simple count query to test connection
        count = await collection.count_documents({})
        
        return {
            "status": "success",
            "message": "Database connection successful",
            "total_sessions": count
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Database connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@router.get("/test-type-prompt/{test_type}")
async def get_test_type_prompt(test_type: str):
    """
    Belirli bir test type'ına göre test_case_main_prompt değerini getirir.
    """
    try:
        logger.info(f"[DEBUG] get_test_type_prompt called with test_type: {test_type}")
        
        db = await get_database()
        collection = db["test_scenario_generation_prompt"]
        
        # Test type'a göre prompt'u ve create prompts'ları bul
        document = await collection.find_one(
            {"test_name": test_type},
            {"test_case_main_prompt": 1, "test_case_create_prompts": 1, "_id": 0}
        )
        
        if not document:
            logger.warning(f"[WARNING] No prompt found for test_type: {test_type}")
            return {
                "status": "error",
                "message": f"No prompt found for test type: {test_type}",
                "prompt": "",
                "create_prompts": {}
            }
        
        prompt = document.get("test_case_main_prompt", "")
        create_prompts = document.get("test_case_create_prompts", {})
        
        logger.info(f"[DEBUG] Found prompt for test_type {test_type}, length: {len(prompt)}")
        logger.info(f"[DEBUG] Found {len(create_prompts)} create prompts")
        
        return {
            "status": "success",
            "test_type": test_type,
            "prompt": prompt,
            "create_prompts": create_prompts
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Error getting test type prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-scenarios/{session_id}")
async def get_test_scenarios_from_output(session_id: str):
    """
    Fetch test scenarios from MongoDB output structure for a specific session.
    Path: processes.test_scenario_generation.output.test_scenarios.TestScenarios
    """
    try:
        db = await get_database()
        collection = db["session_history"]
        
        # Find the document with the specific session_id
        document = await collection.find_one({"session_id": session_id})
        
        if not document:
            logger.warning(f"[TestScenarios] No document found with session_id: {session_id}")
            return {
                "status": "error",
                "message": f"No process found with session_id: {session_id}"
            }
        
        # Navigate to the test scenarios in the output structure
        test_scenarios = []
        
        # Check if the document has the required nested structure
        # Path: processes.test_scenario_generation.output.test_scenarios.TestScenarios
        processes = document.get("processes", {})
        test_scenario_gen = processes.get("test_scenario_generation", {})
        output = test_scenario_gen.get("output", {})
        test_scenarios_obj = output.get("test_scenarios", {})
        
        if "TestScenarios" in test_scenarios_obj:
            raw_scenarios = test_scenarios_obj["TestScenarios"]
            
            # Process each scenario to ensure consistent structure
            for i, scenario in enumerate(raw_scenarios):
                processed_scenario = {
                    "scenario_id": scenario.get("ScenarioID", f"scenario_{i}"),
                    "scenario": scenario.get("Title", f"Scenario {i+1}"),
                    "description": scenario.get("Description", ""),
                    "objective": scenario.get("Objective", ""),
                    "category": scenario.get("Category", ""),
                    "target_symbols": scenario.get("TargetSymbols", []),
                    "setup": scenario.get("Setup", []),
                    "action": scenario.get("Action", ""),
                    "oracle": scenario.get("Oracle", ""),
                    "expected_behavior": scenario.get("ExpectedBehavior", "pass"),
                    "execution_status": scenario.get("ExecutionStatus", ""),
                    "unsupported_reason": scenario.get("UnsupportedReason", ""),
                    "comments": scenario.get("Comments", "")
                }
                test_scenarios.append(processed_scenario)
        
        logger.info(f"[TestScenarios] Found {len(test_scenarios)} test scenarios for session {session_id}")
        
        return {
            "status": "success",
            "test_scenarios": test_scenarios,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error fetching test scenarios for session {session_id}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fetch test scenarios: {str(e)}"
        }

@router.get("/debug/session-structure/{session_id}")
async def debug_session_structure(session_id: str):
    """
    Debug endpoint to check the structure of a session document
    """
    try:
        db = await get_database()
        collection = db["session_history"]
        
        document = await collection.find_one({"session_id": session_id})
        
        if not document:
            return {
                "status": "error",
                "message": f"No document found with session_id: {session_id}"
            }
        
        # Return the structure info
        processes = document.get("processes", {})
        test_scenario_gen = processes.get("test_scenario_generation", {})
        output = test_scenario_gen.get("output", {})
        
        return {
            "status": "success",
            "session_id": session_id,
            "has_processes": "processes" in document,
            "has_test_scenario_generation": "test_scenario_generation" in processes,
            "has_output": "output" in test_scenario_gen,
            "output_keys": list(output.keys()) if output else [],
            "test_scenarios_structure": output.get("test_scenarios", {}) if "test_scenarios" in output else "Not found",
            "full_structure": {
                "processes_keys": list(processes.keys()) if processes else [],
                "test_scenario_gen_keys": list(test_scenario_gen.keys()) if test_scenario_gen else [],
                "output_keys": list(output.keys()) if output else []
            }
        }
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return {
            "status": "error",
            "message": f"Debug failed: {str(e)}"
        }

async def _generate_test_cases_for_scenarios_chunked_legacy(request: Request):
    """
    Generate test cases for selected test scenarios using LM Studio.
    Each selected scenario gets its own POST request.
    """
    try:
        data = await request.json()
        logger.info(f"[TestCaseGeneration] Generate test cases request received")
        
        # Extract data from request
        selected_scenarios = data.get("selected_scenarios", [])
        process_prompt = data.get("process_prompt", "")
        selected_files = data.get("selected_files", [])
        project_structure = data.get("project_structure") or {}
        ai_model = data.get("ai_model", "llama3.2:3b")
        session_id = data.get("session_id", "")
        selected_process_title = data.get("selected_process_title", "")  # Yeni alan
        api_key = data.get("api_key")  # API key extraction
        
        if not selected_scenarios:
            raise HTTPException(status_code=400, detail="No test scenarios selected")
        
        if not process_prompt:
            raise HTTPException(status_code=400, detail="Process prompt is required")
        
        logger.info(f"[TestCaseGeneration] Processing {len(selected_scenarios)} scenarios with model {ai_model}")
        logger.info(f"[TestCaseGeneration] Selected process title: {selected_process_title}")
        logger.info(f"[TestCaseGeneration] API Key: {'SET' if api_key else 'NOT SET'}")
        
        # Initialize LLM client with model name and API key
        from utils.model_client import LLMClient
        try:
            model_client = LLMClient(model_name=ai_model, api_key=api_key, use_case='test_case_generation')  # Initialize with model name and API key
            logger.info(f"[TestCaseGeneration] LLMClient initialized successfully with model: {ai_model}")
        except Exception as e:
            logger.error(f"[TestCaseGeneration] Failed to initialize LLMClient: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize AI model: {str(e)}")
        
        # Prepare file contents and calculate tokens
        file_contents = ""
        source_items = []
        if selected_files:
            for file_info in selected_files:
                file_name = file_info.get("name", "Unknown")
                file_content = file_info.get("content", "")
                file_type = file_info.get("type")
                if is_project_structure_file(file_name, file_type):
                    if not project_structure:
                        project_structure = parse_project_structure(file_content, file_name)
                    continue
                source_items.append({"name": file_name, "content": file_content})
                file_contents += f"\n\n=== FILE: {file_name} ===\n{file_content}\n"
        if not project_structure:
            project_structure = build_project_structure(source_items)
        project_ast_context = project_structure_prompt_context(project_structure)
        
        # Token limit control (same as Test Scenario Generation)
        from utils.text_splitter import count_tokens
        
        # Define token limit at the beginning
        TOKEN_LIMIT = 4000
        
        total_token_count = 0
        if file_contents.strip():
            total_token_count = count_tokens(file_contents)
            logger.info(f"[TestCaseGeneration] Total token count for file contents: {total_token_count}")
            
            # Check token limit
            if total_token_count > TOKEN_LIMIT:
                logger.warning(f"[TestCaseGeneration] Token count ({total_token_count}) exceeds limit ({TOKEN_LIMIT})")
                # Only switch model if it's already a local LM Studio model (not Gemini)
                if not ai_model.startswith("gemini") and ai_model != "qwen2.5-7b-instruct-1m":
                    logger.info(f"[TestCaseGeneration] Switching local model from {ai_model} to qwen2.5-7b-instruct-1m for large content processing")
                    ai_model = "qwen2.5-7b-instruct-1m"  # High-capacity local model for large content
                else:
                    logger.info(f"[TestCaseGeneration] Model {ai_model} already supports large context, no switch needed")
            else:
                logger.info(f"[TestCaseGeneration] Token count ({total_token_count}) is within limit ({TOKEN_LIMIT}), using selected model: {ai_model}")
        
        # Also check process prompt token count
        prompt_token_count = count_tokens(process_prompt) if process_prompt else 0
        total_combined_tokens = total_token_count + prompt_token_count
        
        logger.info(f"[TestCaseGeneration] Process prompt tokens: {prompt_token_count}")
        logger.info(f"[TestCaseGeneration] Combined total tokens: {total_combined_tokens}")
        
        if total_combined_tokens > TOKEN_LIMIT and ai_model != "qwen2.5-7b-instruct-1m":
            logger.warning(f"[TestCaseGeneration] Combined token count ({total_combined_tokens}) exceeds limit, switching to high-capacity model")
            ai_model = "qwen2.5-7b-instruct-1m"
        
        # Initialize LLM client with final model
        actual_model = model_client.get_model_identifier(ai_model)  # Convert frontend key to actual model
        llm_client = LLMClient(model_name=actual_model, api_key=api_key, use_case='test_scenario_generation')  # Use actual model name with API key and speed optimization
        logger.info(f"[TestCaseGeneration] Using model: {ai_model} -> {actual_model}")
        
        test_case_results = []
        
        # Process each scenario separately
        for i, scenario in enumerate(selected_scenarios):
            logger.info(f"[TestCaseGeneration] Processing scenario {i+1}/{len(selected_scenarios)}: {scenario.get('scenario_id', 'Unknown')}")
            
            # Prepare prompt for this specific scenario using the customized process prompt
            json_structure = """{
  "TestCases": [
    {
      "ScenarioID": "<Dynamic Source Scenario ID>",
      "TestCaseID": "<Dynamic Test Case ID>",
      "Title": "<Clear and descriptive test case title>",
      "Description": "<Detailed test case description explaining what is being tested and why it's important>",
      "Objective": "<Specific objective of this test case>",
      "TargetSymbols": ["package.module.Class.method"],
      "Preconditions": ["Concrete executable setup"],
      "TestSteps": ["Concrete call using a declared signature"],
      "ExpectedResult": "Observable value, state, or declared error",
      "OracleType": "return_value/state/error/exception",
      "ExpectedBehavior": "pass or expected_rejection",
      "ExecutionStatus": "executable or unsupported",
      "UnsupportedReason": "Empty when executable; otherwise missing API/observable",
      "Comments": "<Additional notes, assumptions, or considerations>"
    }
  ],
  "Summary": {
    "TotalTestCases": 1,
    "Coverage": "<Brief description of test case coverage>"
  }
}"""
            
            scenario_info = f"""IMPORTANT: You must respond ONLY with valid JSON. Do not include any explanatory text, markdown formatting, or additional content outside the JSON.

{process_prompt}

## SPECIFIC TEST SCENARIO TO GENERATE TEST CASES FOR:

**Scenario ID:** {scenario.get('scenario_id', 'N/A')}
**Title:** {scenario.get('scenario', scenario.get('Title', 'Unknown'))}
**Description:** {scenario.get('description', scenario.get('Description', ''))}
**Objective:** {scenario.get('objective', scenario.get('Objective', ''))}
**Category:** {scenario.get('category', scenario.get('Category', ''))}
**Scenario Target Symbols:** {scenario.get('target_symbols', scenario.get('TargetSymbols', []))}
**Scenario Action:** {scenario.get('action', scenario.get('Action', ''))}
**Scenario Oracle:** {scenario.get('oracle', scenario.get('Oracle', ''))}
**Scenario Execution Status:** {scenario.get('execution_status', scenario.get('ExecutionStatus', ''))}

## APPLICATION CODE/FILES TO ANALYZE:
{file_contents}

{EXECUTION_GROUNDING_RULES}

## PROJECT AST MANIFEST:
{project_ast_context}

## STRICT OUTPUT REQUIREMENTS:
Respond ONLY with a valid JSON object with this EXACT structure (no other text):

"""
            
            instructions = """

## ENHANCED INSTRUCTIONS FOR TEST CASE GENERATION (Token-Optimized):
Generate 7-8 comprehensive test cases specifically for the above test scenario. 
Each test case should cover different aspects.

## ENHANCED REQUIREMENTS FOR TEST CASES:
- Each test case must have unique TestCaseID within the scenario scope
- Categorize properly (Positive, Negative, Boundary, Security, Performance, etc.)
- Add meaningful Comments with assumptions or special considerations

## QUALITY GUIDELINES:
- Focus specifically on the scenario described above
- Ensure each test case is unique and adds value
- Make test cases directly related to the scenario objectives
- Write practical test procedures
- Include comprehensive validation steps
- Every executable case must name at least one exact TargetSymbols entry present in the Project AST manifest or approved robot contract
- Preserve unsupported scenarios as unsupported; never fabricate an implementation path
- Define the oracle before the steps and make ExpectedResult directly assertable
- Consider both functional and non-functional aspects

Generate between 7-8 detailed test cases that thoroughly validate this specific scenario with simplified structure. Start your response immediately with the JSON object."""

            # Combine all parts with token awareness (similar to Test Scenario Generation)
            scenario_prompt = scenario_info + json_structure + instructions
            
            # Additional token check for individual scenario processing
            individual_prompt_tokens = count_tokens(scenario_prompt)
            logger.info(f"[TestCaseGeneration] Individual scenario prompt tokens: {individual_prompt_tokens}")
            
            if individual_prompt_tokens > TOKEN_LIMIT and ai_model != "qwen2.5-7b-instruct-1m":
                logger.warning(f"[TestCaseGeneration] Individual prompt exceeds token limit, ensuring high-capacity model")
                ai_model = "qwen2.5-7b-instruct-1m"
                # Re-initialize LLM client with updated model
                actual_model = model_client.get_model_identifier(ai_model)
                llm_client = LLMClient(model_name=actual_model, api_key=api_key, use_case='test_scenario_generation')
                logger.info(f"[TestCaseGeneration] Updated to model: {ai_model} -> {actual_model}")
            
            try:
                # Send request to LLM
                logger.info(f"[TestCaseGeneration] Sending request to LLM for scenario {scenario.get('scenario_id', 'Unknown')}")
                
                # Try JSON format first (like Test Scenario Generation)
                try:
                    response = await llm_client.generate_response(
                        scenario_prompt,
                        temperature=0.2,  # Consistent with Test Scenario Generation
                        max_tokens=6000,
                        response_format={"type": "json_object"}  # Force JSON format
                    )
                except Exception as json_format_error:
                    logger.warning(f"[TestCaseGeneration] JSON format not supported, falling back to normal mode: {json_format_error}")
                    # Fallback: Normal mode
                    response = await llm_client.generate_response(
                        scenario_prompt,
                        temperature=0.2,
                        max_tokens=6000
                    )
                
                if not response:
                    raise ValueError("No response from LLM")
                
                logger.info(f"[TestCaseGeneration] Received LLM response length: {len(response)}")
                
                # Enhanced JSON parsing with robust fallback mechanisms
                try:
                    import re
                    import json
                    
                    logger.info(f"[TestCaseGeneration] Raw LLM response (first 500 chars): {response[:500]}")
                    
                    # 1. Start with clean response
                    cleaned_response = response.strip()
                    
                    # 2. Remove markdown code blocks
                    if '```json' in cleaned_response:
                        json_blocks = re.findall(r'```json\s*(.*?)\s*```', cleaned_response, re.DOTALL)
                        if json_blocks:
                            cleaned_response = json_blocks[0].strip()
                            logger.info(f"[TestCaseGeneration] Extracted JSON from markdown block")
                    elif '```' in cleaned_response:
                        cleaned_response = re.sub(r'```.*?```', '', cleaned_response, flags=re.DOTALL).strip()
                        
                    # 3. Remove explanatory text before JSON
                    lines = cleaned_response.split('\n')
                    json_started = False
                    json_lines = []
                    brace_count = 0
                    
                    for line in lines:
                        stripped_line = line.strip()
                        if stripped_line.startswith('{') or json_started:
                            json_started = True
                            json_lines.append(line)
                            brace_count += stripped_line.count('{') - stripped_line.count('}')
                            
                            # Stop when braces are balanced and we have a complete object
                            if brace_count == 0 and json_started and stripped_line.endswith('}'):
                                break
                    
                    if json_lines:
                        cleaned_response = '\n'.join(json_lines)
                        logger.info(f"[TestCaseGeneration] Extracted JSON lines, result length: {len(cleaned_response)}")
                    
                    # 4. Try JSON parsing with cleaned response
                    try:
                        test_case_response = json.loads(cleaned_response)
                        logger.info(f"[TestCaseGeneration] Successfully parsed cleaned JSON")
                        
                    except json.JSONDecodeError as initial_error:
                        logger.warning(f"[TestCaseGeneration] Initial JSON parsing failed: {initial_error}")
                        
                        # 5. Enhanced regex with multiple patterns
                        json_patterns = [
                            r'\{[\s\S]*?"TestCases"[\s\S]*?\}(?=\s*$)',  # Full JSON object until end
                            r'\{[\s\S]*?"TestCases"[\s\S]*?\}',  # Basic pattern
                            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested braces pattern
                        ]
                        
                        best_match = None
                        for pattern in json_patterns:
                            json_matches = list(re.finditer(pattern, response, re.MULTILINE))
                            
                            for match in json_matches:
                                candidate = match.group(0).strip()
                                
                                # Check brace balance
                                open_braces = candidate.count('{')
                                close_braces = candidate.count('}')
                                
                                if open_braces == close_braces:
                                    try:
                                        # Test if it's valid JSON
                                        json.loads(candidate)
                                        best_match = candidate
                                        logger.info(f"[TestCaseGeneration] Found valid JSON with pattern {pattern}")
                                        break
                                    except json.JSONDecodeError:
                                        continue
                                elif open_braces > close_braces:
                                    # Add missing closing braces
                                    missing = open_braces - close_braces
                                    candidate += '}' * missing
                                    try:
                                        json.loads(candidate)
                                        best_match = candidate
                                        logger.info(f"[TestCaseGeneration] Fixed and validated JSON with missing braces")
                                        break
                                    except json.JSONDecodeError:
                                        continue
                            
                            if best_match:
                                break
                        
                        if best_match:
                            test_case_response = json.loads(best_match)
                        else:
                            # 6. Create fallback JSON structure when parsing completely fails
                            logger.warning(f"[TestCaseGeneration] All JSON parsing attempts failed, creating fallback structure")
                            raise json.JSONDecodeError("Could not parse response as JSON", response, 0)
                    
                    # Enhanced validation and structure completion
                    if "TestCases" not in test_case_response:
                        raise ValueError("TestCases key not found in response")
                    
                    test_cases = test_case_response["TestCases"]
                    if not isinstance(test_cases, list):
                        raise ValueError("TestCases must be a list")
                    
                    # Enhance each test case with missing required fields
                    scenario_id = scenario.get('scenario_id', f'scenario_{i}')
                    scenario_title = scenario.get('scenario', scenario.get('Title', 'Unknown'))
                    
                    enhanced_test_cases = []
                    for idx, tc in enumerate(test_cases):
                        # Ensure all required fields are present with defaults
                        enhanced_tc = {
                            "ScenarioID": tc.get("ScenarioID", scenario_id),
                            "TestCaseID": tc.get("TestCaseID", f"{scenario_id}_TC_{idx+1:03d}"),
                            "Title": tc.get("Title", f"Test Case {idx+1} for {scenario_title}"),
                            "Description": tc.get("Description", f"Test case for validating {scenario_title}"),
                            "Objective": tc.get("Objective", f"Verify functionality of {scenario_title}"),
                            "Category": tc.get("Category", "Positive"),
                            "TargetSymbols": tc.get("TargetSymbols", []),
                            "Preconditions": tc.get("Preconditions", []),
                            "TestSteps": tc.get("TestSteps", []),
                            "ExpectedResult": tc.get("ExpectedResult", ""),
                            "OracleType": tc.get("OracleType", ""),
                            "ExpectedBehavior": tc.get("ExpectedBehavior", "pass"),
                            "ExecutionStatus": tc.get("ExecutionStatus", "unsupported" if not tc.get("TargetSymbols") else "executable"),
                            "UnsupportedReason": tc.get("UnsupportedReason", "No declared target symbol was supplied" if not tc.get("TargetSymbols") else ""),
                            "Comments": tc.get("Comments", "Review and enhance as needed")
                        }
                        enhanced_test_cases.append(enhanced_tc)
                    
                    # Update the response with enhanced test cases
                    test_case_response["TestCases"] = enhanced_test_cases
                    test_cases = enhanced_test_cases
                    
                    logger.info(f"[TestCaseGeneration] Enhanced and validated {len(test_cases)} test cases")
                    
                    # Add summary if not present
                    if "Summary" not in test_case_response:
                        categories = {}
                        for tc in test_cases:
                            cat = tc.get("Category", "Unknown")
                            categories[cat] = categories.get(cat, 0) + 1
                        
                        test_case_response["Summary"] = {
                            "TotalTestCases": len(test_cases),
                            "Categories": categories,
                            "ScenarioID": scenario.get('scenario_id', f'scenario_{i}'),
                            "Coverage": f"Generated {len(test_cases)} test cases covering various aspects"
                        }
                    
                    # Ensure each test case has the required scenario ID
                    for tc in test_cases:
                        if not tc.get("ScenarioID"):
                            tc["ScenarioID"] = scenario.get('scenario_id', f'scenario_{i}')
                    
                    logger.info(f"[TestCaseGeneration] Successfully parsed {len(test_cases)} test cases for scenario {scenario.get('scenario_id', 'Unknown')}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"[TestCaseGeneration] Failed to parse JSON response: {e}")
                    logger.error(f"[TestCaseGeneration] Response preview: {response[:500]}")
                    
                    # Create fallback test cases by extracting information from raw text
                    logger.info(f"[TestCaseGeneration] Creating fallback test cases from text response")
                    
                    scenario_id = scenario.get('scenario_id', f'scenario_{i}')
                    scenario_title = scenario.get('scenario', scenario.get('Title', 'Unknown'))
                    
                    # Try to extract test case information from text
                    fallback_test_cases = []
                    
                    # Look for test case patterns in the response
                    test_case_patterns = [
                        r'(?i)test\s*case\s*\d*[:\-\s]*([^\n]+)',
                        r'(?i)title[:\-\s]*([^\n]+)',
                        r'(?i)scenario[:\-\s]*([^\n]+)',
                    ]
                    
                    extracted_titles = []
                    for pattern in test_case_patterns:
                        matches = re.findall(pattern, response)
                        extracted_titles.extend([match.strip() for match in matches if match.strip()])
                    
                    # Remove duplicates and filter
                    unique_titles = list(set(extracted_titles))[:5]  # Limit to 5
                    
                    if not unique_titles:
                        # Generate generic test cases
                        unique_titles = [
                            f"Basic functionality test for {scenario_title}",
                            f"Positive validation test for {scenario_title}",
                            f"Negative test case for {scenario_title}",
                            f"Boundary value test for {scenario_title}",
                            f"Error handling test for {scenario_title}"
                        ]
                    
                    # Create fallback test cases with enhanced structure
                    for idx, title in enumerate(unique_titles[:5]):
                        test_case = {
                            "ScenarioID": scenario_id,
                            "TestCaseID": f"{scenario_id}_TC_{idx+1:03d}",
                            "Title": title,
                            "Description": f"Comprehensive test case for validating {scenario_title}. This test case was auto-generated from the scenario requirements.",
                            "Objective": f"Verify the functionality and behavior of {scenario_title}",
                            "Category": "Positive",
                            "TargetSymbols": [],
                            "Preconditions": [],
                            "TestSteps": [],
                            "ExpectedResult": "",
                            "OracleType": "",
                            "ExpectedBehavior": "pass",
                            "ExecutionStatus": "unsupported",
                            "UnsupportedReason": "The LLM response could not be parsed into an execution-grounded test case.",
                            "Comments": "Auto-generated test case. Please review and enhance based on specific requirements."
                        }
                        fallback_test_cases.append(test_case)
                    
                    # Create fallback response structure
                    test_case_response = {
                        "TestCases": fallback_test_cases,
                        "Summary": {
                            "TotalTestCases": len(fallback_test_cases),
                            "Categories": {tc["Category"]: 1 for tc in fallback_test_cases},
                            "Coverage": f"Fallback test cases generated for {scenario_title}",
                            "Note": "Generated from text parsing due to JSON parsing failure"
                        }
                    }
                    
                    test_cases = test_case_response["TestCases"]
                    logger.info(f"[TestCaseGeneration] Created {len(test_cases)} fallback test cases")
                    
                except Exception as parse_error:
                    logger.error(f"[TestCaseGeneration] Error during JSON parsing and fallback: {parse_error}")
                    
                    # Last resort: Single generic test case
                    scenario_id = scenario.get('scenario_id', f'scenario_{i}')
                    scenario_title = scenario.get('scenario', scenario.get('Title', 'Unknown'))
                    
                    fallback_test_case = {
                        "ScenarioID": scenario_id,
                        "TestCaseID": f"{scenario_id}_TC_001",
                        "Title": f"General test case for {scenario_title}",
                        "Description": f"Basic test case generated for {scenario_title}",
                        "Objective": f"Verify basic functionality of {scenario_title}",
                        "Category": "Positive",
                        "TargetSymbols": [],
                        "Preconditions": [],
                        "TestSteps": [],
                        "ExpectedResult": "",
                        "OracleType": "",
                        "ExpectedBehavior": "pass",
                        "ExecutionStatus": "unsupported",
                        "UnsupportedReason": "Generation failed before an executable target and oracle could be established.",
                        "Comments": "Emergency fallback test case"
                    }
                    
                    test_case_response = {
                        "TestCases": [fallback_test_case],
                        "Summary": {
                            "TotalTestCases": 1,
                            "Coverage": "Emergency fallback test case"
                        }
                    }
                    
                    test_cases = test_case_response["TestCases"]
                    logger.info(f"[TestCaseGeneration] Created emergency fallback test case")
                
                # Return the successfully parsed test cases
                if test_cases:
                    result = {
                        "scenario_id": scenario.get('scenario_id', f'scenario_{i}'),
                        "scenario_title": scenario.get('scenario', scenario.get('Title', 'Unknown')),
                        "status": "success",
                        "test_cases": test_cases,
                        "test_cases_count": len(test_cases),
                        "model_used": ai_model,
                        "summary": test_case_response.get("Summary", {})
                    }
                    
                else:
                    result = {
                        "scenario_id": scenario.get('scenario_id', f'scenario_{i}'),
                        "scenario_title": scenario.get('scenario', scenario.get('Title', 'Unknown')),
                        "status": "error",
                        "error": "No response from LLM",
                        "test_cases": [],
                        "test_cases_count": 0,
                        "model_used": ai_model
                    }
                
            except Exception as e:
                logger.error(f"[TestCaseGeneration] Error processing scenario {scenario.get('scenario_id', 'Unknown')}: {str(e)}")
                result = {
                    "scenario_id": scenario.get('scenario_id', f'scenario_{i}'),
                    "scenario_title": scenario.get('scenario', scenario.get('Title', 'Unknown')),
                    "status": "error",
                    "error": str(e),
                    "test_cases": [],
                    "test_cases_count": 0,
                    "model_used": ai_model
                }
            
            test_case_results.append(result)
        
        # Save results to database if session_id is provided
        if session_id:
            try:
                db = await get_database()
                collection = db["session_history"]
                
                # Update the session document with test case generation results
                update_result = await collection.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {
                            "processes.test_case_generation.output": {
                                "test_case_results": test_case_results,
                                "project_structure": project_structure,
                                "metadata": {
                                    "generated_at": datetime.utcnow(),
                                    "scenarios_processed": len(selected_scenarios),
                                    "total_test_cases": sum(r.get("test_cases_count", 0) for r in test_case_results),
                                    "model_used": ai_model,
                                    "session_id": session_id,
                                    "selected_process_title": selected_process_title  # Yeni alan
                                }
                            },
                            "processes.test_case_generation.selected_process_title": selected_process_title,  # Ana seviyede de kaydet
                            "updated_at": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                
                logger.info(f"[TestCaseGeneration] Saved results to database for session {session_id}")
                
            except Exception as e:
                logger.error(f"[TestCaseGeneration] Failed to save results to database: {str(e)}")
        
        # Return comprehensive results
        total_test_cases = sum(r.get("test_cases_count", 0) for r in test_case_results)
        successful_scenarios = sum(1 for r in test_case_results if r.get("status") == "success")
        
        logger.info(f"[TestCaseGeneration] Completed: {successful_scenarios}/{len(selected_scenarios)} scenarios, {total_test_cases} total test cases")
        
        return {
            "status": "success",
            "test_case_results": test_case_results,
            "project_structure": project_structure,
            "summary": {
                "scenarios_processed": len(selected_scenarios),
                "successful_scenarios": successful_scenarios,
                "failed_scenarios": len(selected_scenarios) - successful_scenarios,
                "total_test_cases": total_test_cases,
                "model_used": ai_model,
                "session_id": session_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TestCaseGeneration] Error in generate_test_cases_for_scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


TEST_CASE_CONTEXT_SWITCH_THRESHOLD = 64_000
TEST_CASE_LARGE_CONTEXT_MODEL = "qwen2.5-7b-instruct-1m"
EXPECTED_TEST_CASES_PER_SCENARIO = 8
ESTIMATED_TOKENS_PER_TEST_CASE = 300


def _select_test_case_model(selected_model: str, input_tokens: int) -> str:
    """Keep the selected model through 64k input tokens.

    API-backed Gemini models are never silently replaced with a local model.
    """
    if (
        input_tokens > TEST_CASE_CONTEXT_SWITCH_THRESHOLD
        and not selected_model.lower().startswith("gemini")
    ):
        return TEST_CASE_LARGE_CONTEXT_MODEL
    return selected_model


def _parse_test_case_json(response: str) -> Dict:
    """Extract and normalize grouped or common small-model JSON variants."""
    import re

    cleaned = response.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        decoder = json.JSONDecoder()
        if start < 0:
            raise
        parsed, _ = decoder.raw_decode(cleaned[start:])
    if isinstance(parsed, list):
        parsed = {"TestCases": parsed}
    if not isinstance(parsed, dict):
        raise ValueError("LLM response must contain a JSON object or array")

    # Small local models frequently preserve the requested structure while
    # changing key casing/style. Normalize those harmless variations without
    # accepting arbitrary prose or inventing test-case content.
    for wrapper_key in ("result", "Result", "output", "Output", "data", "Data"):
        wrapped = parsed.get(wrapper_key)
        if isinstance(wrapped, dict):
            parsed = {**wrapped, "Summary": wrapped.get("Summary", parsed.get("Summary", {}))}
            break

    scenario_results = next((
        parsed.get(key)
        for key in ("ScenarioResults", "scenario_results", "scenarioResults", "scenarios")
        if isinstance(parsed.get(key), list)
    ), None)
    if scenario_results is not None:
        normalized_results = []
        for result in scenario_results:
            if not isinstance(result, dict):
                continue
            cases = next((
                result.get(key)
                for key in ("TestCases", "test_cases", "testCases", "cases")
                if isinstance(result.get(key), list)
            ), [])
            normalized_results.append({
                **result,
                "ScenarioID": (
                    result.get("ScenarioID")
                    or result.get("scenario_id")
                    or result.get("scenarioId")
                    or ""
                ),
                "TestCases": cases,
            })
        return {
            **parsed,
            "ScenarioResults": normalized_results,
            "Summary": parsed.get("Summary", parsed.get("summary", {})),
        }

    test_cases = next((
        parsed.get(key)
        for key in ("TestCases", "test_cases", "testCases", "cases")
        if isinstance(parsed.get(key), list)
    ), None)
    if test_cases is None:
        raise ValueError(
            "LLM response must contain ScenarioResults or TestCases "
            f"(received keys: {sorted(str(key) for key in parsed)})"
        )

    grouped: Dict[str, List[Dict]] = {}
    for case in test_cases:
        if not isinstance(case, dict):
            continue
        scenario_id = str(
            case.get("ScenarioID")
            or case.get("scenario_id")
            or case.get("scenarioId")
            or ""
        )
        grouped.setdefault(scenario_id, []).append(case)
    return {
        "ScenarioResults": [
            {"ScenarioID": scenario_id, "TestCases": cases}
            for scenario_id, cases in grouped.items()
        ],
        "Summary": parsed.get("Summary", parsed.get("summary", {})),
    }


def _group_cases_by_scenario(parsed: Dict, scenario_ids: List[str]) -> Dict[str, List[Dict]]:
    """Accept only requested IDs; a blank ID is safe only for one scenario."""
    grouped = {scenario_id: [] for scenario_id in scenario_ids}
    for result in parsed.get("ScenarioResults", []):
        if not isinstance(result, dict):
            continue
        scenario_id = str(result.get("ScenarioID") or "")
        if not scenario_id and len(scenario_ids) == 1:
            scenario_id = scenario_ids[0]
        if scenario_id not in grouped or not isinstance(result.get("TestCases"), list):
            continue
        grouped[scenario_id].extend(
            case for case in result["TestCases"] if isinstance(case, dict)
        )
    return grouped


def _unsupported_test_case(scenario_id: str, title: str, reason: str) -> Dict:
    """Keep an omitted scenario visible without inventing executable behavior."""
    return {
        "ScenarioID": scenario_id,
        "TestCaseID": f"{scenario_id}_UNSUPPORTED_001",
        "Title": f"Execution grounding required for {title}",
        "Description": (
            "The model could not produce an execution-grounded test case for this "
            "scenario after coverage validation and one repair attempt."
        ),
        "Objective": f"Identify the missing executable context for {title}",
        "Category": "Grounding Gap",
        "TargetSymbols": [],
        "Preconditions": [],
        "TestSteps": [],
        "ExpectedResult": "Provide the target AST symbol and relevant source implementation.",
        "OracleType": "context_required",
        "ExpectedBehavior": "unsupported",
        "ExecutionStatus": "unsupported",
        "UnsupportedReason": reason,
        "Comments": "Diagnostic placeholder; do not generate or execute test code from this item.",
        "IsDiagnostic": True,
    }


async def _generate_test_cases_for_scenarios_impl(request: Request):
    """Generate every selected scenario in one model call and one context."""
    try:
        data = await request.json()
        selected_scenarios = data.get("selected_scenarios", [])
        process_prompt = data.get("process_prompt", "")
        selected_files = data.get("selected_files", [])
        project_structure = data.get("project_structure") or {}
        selected_model = data.get("ai_model", "llama3.2:3b")
        session_id = data.get("session_id", "")
        selected_process_title = data.get("selected_process_title", "")
        api_key = data.get("api_key")

        if not selected_scenarios:
            raise HTTPException(status_code=400, detail="No test scenarios selected")
        if not process_prompt:
            raise HTTPException(status_code=400, detail="Process prompt is required")

        source_items = []
        file_sections = []
        for file_info in selected_files:
            file_name = file_info.get("name", "Unknown")
            file_content = file_info.get("content", "")
            if is_project_structure_file(file_name, file_info.get("type")):
                if not project_structure:
                    project_structure = parse_project_structure(file_content, file_name)
                continue
            source_items.append({"name": file_name, "content": file_content})
            file_sections.append(f"=== FILE: {file_name} ===\n{file_content}")
        if not project_structure:
            project_structure = build_project_structure(source_items)

        scenarios_json = json.dumps(selected_scenarios, ensure_ascii=False, indent=2)
        file_contents = "\n\n".join(file_sections)
        project_ast_context = project_structure_prompt_context(project_structure)
        unified_prompt = f"""IMPORTANT: Respond ONLY with one valid JSON object. Generate all test cases for all scenarios in this single request.

{process_prompt}

## SELECTED TEST SCENARIOS
{scenarios_json}

## APPLICATION SOURCE (may be empty when the compact Project AST is supplied)
{file_contents}

{EXECUTION_GROUNDING_RULES}

## WHOLE-PROJECT AST MANIFEST
{project_ast_context}

## OUTPUT CONTRACT
Return exactly:
{{"ScenarioResults":[{{"ScenarioID":"<exact supplied ID>","TestCases":[...]}}],"Summary":{{"TotalTestCases":number,"Coverage":string}}}}.
Include every supplied ScenarioID exactly once and keep its cases inside that scenario object.
Generate 7-8 distinct cases per supplied scenario. Every case must include:
ScenarioID, TestCaseID, Title, Description, Objective, Category, TargetSymbols,
Preconditions, TestSteps, ExpectedResult, OracleType, ExpectedBehavior,
ExecutionStatus, UnsupportedReason, and Comments.
ScenarioID must exactly match the source scenario. Never omit a scenario or return an empty TestCases array.
If a scenario cannot be grounded in the AST/source, return one case with ExecutionStatus="unsupported"
and a precise UnsupportedReason instead of inventing behavior or omitting the scenario.
Do not split, summarize, or defer any scenario to another request.
"""

        from utils.text_splitter import count_tokens
        input_tokens = count_tokens(unified_prompt)
        ai_model = _select_test_case_model(selected_model, input_tokens)
        if ai_model != selected_model:
            logger.warning(
                "[TestCaseGeneration] Unified input has %s tokens (> %s); switching %s to %s",
                input_tokens,
                TEST_CASE_CONTEXT_SWITCH_THRESHOLD,
                selected_model,
                ai_model,
            )
        else:
            logger.info(
                "[TestCaseGeneration] Unified input has %s tokens; keeping selected model %s",
                input_tokens,
                selected_model,
            )

        mapper = LLMClient(model_name=ai_model, api_key=api_key, use_case="test_case_generation")
        actual_model = mapper.get_model_identifier(ai_model)
        llm_client = (
            mapper
            if mapper.model_name == actual_model
            else LLMClient(model_name=actual_model, api_key=api_key, use_case="test_case_generation")
        )
        model_context_length = None
        if not ai_model.lower().startswith("gemini"):
            model_context_length = await llm_client.get_model_context_length(actual_model)
        requested_output_tokens = (
            len(selected_scenarios)
            * EXPECTED_TEST_CASES_PER_SCENARIO
            * ESTIMATED_TOKENS_PER_TEST_CASE
        )
        requested_total_tokens = input_tokens + requested_output_tokens
        capacity_warning = bool(
            model_context_length and requested_total_tokens > model_context_length
        )
        target_cases_per_scenario = EXPECTED_TEST_CASES_PER_SCENARIO
        capacity_adapted = False
        if capacity_warning:
            available_output_tokens = max(1000, model_context_length - input_tokens - 1000)
            target_cases_per_scenario = max(1, min(
                EXPECTED_TEST_CASES_PER_SCENARIO,
                available_output_tokens
                // max(1, len(selected_scenarios) * ESTIMATED_TOKENS_PER_TEST_CASE),
            ))
            capacity_adapted = target_cases_per_scenario < EXPECTED_TEST_CASES_PER_SCENARIO
            if capacity_adapted:
                unified_prompt = unified_prompt.replace(
                    "Generate 7-8 distinct cases per supplied scenario.",
                    f"Generate {target_cases_per_scenario} distinct cases per supplied scenario to stay within the selected model's context capacity.",
                )
                input_tokens = count_tokens(unified_prompt)
            logger.warning(
                "[TestCaseGeneration] Estimated input+output demand %s exceeds %s context (%s)",
                requested_total_tokens,
                actual_model,
                model_context_length,
            )
        estimated_output_tokens = (
            len(selected_scenarios)
            * target_cases_per_scenario
            * ESTIMATED_TOKENS_PER_TEST_CASE
        )
        estimated_total_tokens = input_tokens + estimated_output_tokens
        available_generation_tokens = (
            max(1000, model_context_length - input_tokens - 500)
            if model_context_length
            else 24000
        )
        generation_max_tokens = min(
            24000,
            available_generation_tokens,
            max(4000, estimated_output_tokens + 1000),
        )
        response = await llm_client.generate_response(
            unified_prompt,
            temperature=0.2,
            max_tokens=generation_max_tokens,
            skip_chunking=True,
        )
        if not response:
            raise ValueError("No response from LLM")
        schema_repair_attempted = False
        schema_repair_succeeded = False
        schema_repair_error = ""
        try:
            parsed = _parse_test_case_json(response)
        except (ValueError, json.JSONDecodeError) as exc:
            schema_repair_attempted = True
            schema_repair_prompt = f"""Your previous response did not satisfy the test-case JSON schema: {exc}

Generate the test cases now. Do not repeat or summarize the scenario object.

## SCENARIOS
{scenarios_json}

## APPLICATION SOURCE
{file_contents}

{EXECUTION_GROUNDING_RULES}

Return ONLY one valid JSON object in this simpler form:
{{"TestCases":[{{"ScenarioID":"<exact supplied ID>","TestCaseID":"TC_001","Title":"...","Description":"...","Objective":"...","Category":"...","TargetSymbols":["declared.symbol"],"Preconditions":[],"TestSteps":[],"ExpectedResult":"...","OracleType":"...","ExpectedBehavior":"pass","ExecutionStatus":"executable","UnsupportedReason":"","Comments":""}}],"Summary":{{"TotalTestCases":1,"Coverage":"..."}}}}

Generate {target_cases_per_scenario} grounded cases per scenario. Every case must use an exact supplied ScenarioID.
If grounding is impossible, return one TestCases item with ExecutionStatus="unsupported" and a precise UnsupportedReason.
"""
            try:
                repaired_response = await llm_client.generate_response(
                    schema_repair_prompt,
                    temperature=0.1,
                    max_tokens=generation_max_tokens,
                    skip_chunking=True,
                )
                parsed = _parse_test_case_json(repaired_response)
                schema_repair_succeeded = True
            except Exception as repair_exc:
                schema_repair_error = str(repair_exc)
                raise ValueError(
                    f"Test-case schema repair failed after invalid model response: {repair_exc}"
                ) from repair_exc

        scenario_lookup = {}
        scenario_order = []
        for index, scenario in enumerate(selected_scenarios):
            scenario_id = str(
                scenario.get("scenario_id") or scenario.get("ScenarioID") or f"scenario_{index}"
            )
            scenario_lookup[scenario_id] = scenario
            scenario_order.append(scenario_id)

        grouped = _group_cases_by_scenario(parsed, scenario_order)
        missing_before_repair = [
            scenario_id for scenario_id in scenario_order if not grouped[scenario_id]
        ]
        # A single ``unsupported`` case is also an underfilled result when the
        # scenario explicitly targets a symbol that exists in the project AST.
        # Give the model one focused retry with mocking/spying guidance instead
        # of accepting an incorrect unsupported downgrade as successful output.
        symbol_index = set((project_structure or {}).get("symbol_index") or [])
        minimum_case_count = max(1, target_cases_per_scenario - 1)
        underfilled_before_repair = []
        for scenario_id in scenario_order:
            scenario = scenario_lookup[scenario_id]
            scenario_targets = scenario.get("TargetSymbols") or scenario.get("target_symbols") or []
            target_is_grounded = any(str(target) in symbol_index for target in scenario_targets)
            executable_intent = str(
                scenario.get("ExecutionStatus") or scenario.get("execution_status") or "executable"
            ).lower() != "unsupported"
            executable_cases = [
                case for case in grouped[scenario_id]
                if str(case.get("ExecutionStatus", "executable")).lower() != "unsupported"
            ]
            if (
                grouped[scenario_id]
                and target_is_grounded
                and executable_intent
                and len(executable_cases) < minimum_case_count
            ):
                underfilled_before_repair.append(scenario_id)

        repair_scenario_ids = list(dict.fromkeys(
            missing_before_repair + underfilled_before_repair
        ))
        repair_attempted = bool(repair_scenario_ids)
        repair_succeeded_ids: List[str] = []
        repair_error = ""
        if repair_scenario_ids:
            repair_scenarios = [scenario_lookup[item] for item in repair_scenario_ids]
            repair_prompt = f"""Your previous response omitted or underfilled required scenarios. Regenerate only the scenarios below in one response.

## MISSING SCENARIOS
{json.dumps(repair_scenarios, ensure_ascii=False, indent=2)}

## ORIGINAL TEST CASE INSTRUCTIONS
{process_prompt}

## APPLICATION SOURCE
{file_contents}

{EXECUTION_GROUNDING_RULES}

## WHOLE-PROJECT AST MANIFEST
{project_ast_context}

Return only {{"ScenarioResults":[{{"ScenarioID":"<exact missing ID>","TestCases":[...]}}],"Summary":{{}}}}.
Include every missing ID exactly once. Generate {target_cases_per_scenario} grounded cases per scenario.
The target symbols below exist in the supplied Project AST. Logger calls, planner results,
wait methods, and other declared collaborators are observable with mocks/spies. Treat those
as executable test seams; do not mark them unsupported merely because they require patching.
If grounding is impossible, return one explicit ExecutionStatus="unsupported" case with the missing context in UnsupportedReason.
Never return an empty TestCases array.
"""
            try:
                repair_response = await llm_client.generate_response(
                    repair_prompt,
                    temperature=0.1,
                    max_tokens=min(
                        24000,
                        max(4000, len(repair_scenario_ids) * target_cases_per_scenario * ESTIMATED_TOKENS_PER_TEST_CASE),
                    ),
                    skip_chunking=True,
                )
                repaired = _group_cases_by_scenario(
                    _parse_test_case_json(repair_response), repair_scenario_ids
                )
                for scenario_id, cases in repaired.items():
                    if cases:
                        grouped[scenario_id] = cases
                        repair_succeeded_ids.append(scenario_id)
            except Exception as exc:
                repair_error = str(exc)
                logger.warning("[TestCaseGeneration] Coverage repair failed: %s", exc)

        missing_after_repair = [
            scenario_id for scenario_id in scenario_order if not grouped[scenario_id]
        ]
        for scenario_id in missing_after_repair:
            scenario = scenario_lookup[scenario_id]
            title = scenario.get("scenario", scenario.get("Title", "Unknown"))
            grouped[scenario_id].append(_unsupported_test_case(
                scenario_id,
                title,
                "The model omitted this ScenarioID from both the initial unified response and the coverage repair response. Provide the matching Project AST target and relevant source file.",
            ))

        for scenario_id in scenario_order:
            scenario = scenario_lookup[scenario_id]
            title = scenario.get("scenario", scenario.get("Title", "Unknown"))
            enhanced_cases = []
            for index, case in enumerate(grouped[scenario_id]):
                number = index + 1
                targets = case.get("TargetSymbols") or []
                enhanced_cases.append({
                    **case,
                    "ScenarioID": scenario_id,
                    "TestCaseID": case.get("TestCaseID") or f"{scenario_id}_TC_{number:03d}",
                    "Title": case.get("Title") or f"Test Case {number} for {title}",
                    "Description": case.get("Description") or f"Test case for validating {title}",
                    "Objective": case.get("Objective") or f"Verify {title}",
                    "Category": case.get("Category", "Positive"),
                    "TargetSymbols": targets,
                    "Preconditions": case.get("Preconditions", []),
                    "TestSteps": case.get("TestSteps", []),
                    "ExpectedResult": case.get("ExpectedResult", ""),
                    "OracleType": case.get("OracleType", ""),
                    "ExpectedBehavior": case.get("ExpectedBehavior", "pass"),
                    "ExecutionStatus": case.get("ExecutionStatus", "executable" if targets else "unsupported"),
                    "UnsupportedReason": case.get("UnsupportedReason", "" if targets else "No declared target symbol was supplied"),
                    "Comments": case.get("Comments", ""),
                })
            grouped[scenario_id] = enhanced_cases

        test_case_results = []
        for scenario_id in scenario_order:
            scenario = scenario_lookup[scenario_id]
            cases = grouped[scenario_id]
            only_unsupported = all(
                case.get("ExecutionStatus") == "unsupported" for case in cases
            )
            test_case_results.append({
                "scenario_id": scenario_id,
                "scenario_title": scenario.get("scenario", scenario.get("Title", "Unknown")),
                "status": "unsupported" if only_unsupported else "success",
                "grounding_status": "unsupported" if only_unsupported else "grounded",
                "repair_applied": scenario_id in repair_succeeded_ids,
                "test_cases": cases,
                "test_cases_count": len(cases),
                "model_used": ai_model,
                "summary": {
                    "TotalTestCases": len(cases),
                    "Coverage": parsed.get("Summary", {}).get("Coverage", ""),
                },
            })

        total_test_cases = sum(item["test_cases_count"] for item in test_case_results)
        successful_scenarios = sum(item["status"] == "success" for item in test_case_results)
        unsupported_scenarios = sum(item["status"] == "unsupported" for item in test_case_results)
        failed_scenarios = sum(item["status"] == "error" for item in test_case_results)
        output = {
            "test_case_results": test_case_results,
            "project_structure": project_structure,
            "metadata": {
                "generated_at": datetime.utcnow(),
                "scenarios_processed": len(selected_scenarios),
                "total_test_cases": total_test_cases,
                "model_used": ai_model,
                "selected_model": selected_model,
                "input_tokens": input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "estimated_total_tokens": estimated_total_tokens,
                "requested_total_tokens": requested_total_tokens,
                "model_context_length": model_context_length,
                "capacity_warning": capacity_warning,
                "capacity_adapted": capacity_adapted,
                "target_cases_per_scenario": target_cases_per_scenario,
                "generation_max_tokens": generation_max_tokens,
                "generation_mode": "single_context_with_coverage_repair",
                "schema_repair_attempted": schema_repair_attempted,
                "schema_repair_succeeded": schema_repair_succeeded,
                "schema_repair_error": schema_repair_error,
                "repair_attempted": repair_attempted,
                "underfilled_before_repair": underfilled_before_repair,
                "repair_succeeded_ids": repair_succeeded_ids,
                "missing_after_repair": missing_after_repair,
                "repair_error": repair_error,
                "grounding_inputs": {
                    "project_ast_available": bool(
                        project_structure.get("files") or project_structure.get("project_files")
                    ),
                    "project_ast_source": project_structure.get("source", "generated"),
                    "source_file_count": len(source_items),
                    "source_files": [item["name"] for item in source_items],
                },
                "session_id": session_id,
                "selected_process_title": selected_process_title,
            },
        }
        if session_id:
            try:
                db = await get_database()
                await db["session_history"].update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "processes.test_case_generation.output": output,
                        "processes.test_case_generation.selected_process_title": selected_process_title,
                        "updated_at": datetime.utcnow(),
                    }},
                    upsert=True,
                )
            except Exception as exc:
                logger.error("[TestCaseGeneration] Failed to save results: %s", exc)

        return {
            "status": "success",
            **output,
            "summary": {
                "scenarios_processed": len(selected_scenarios),
                "successful_scenarios": successful_scenarios,
                "failed_scenarios": failed_scenarios,
                "unsupported_scenarios": unsupported_scenarios,
                "total_test_cases": total_test_cases,
                "model_used": ai_model,
                "selected_model": selected_model,
                "input_tokens": input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "estimated_total_tokens": estimated_total_tokens,
                "requested_total_tokens": requested_total_tokens,
                "model_context_length": model_context_length,
                "capacity_warning": capacity_warning,
                "capacity_adapted": capacity_adapted,
                "target_cases_per_scenario": target_cases_per_scenario,
                "generation_mode": "single_context_with_coverage_repair",
                "schema_repair_attempted": schema_repair_attempted,
                "schema_repair_succeeded": schema_repair_succeeded,
                "schema_repair_error": schema_repair_error,
                "repair_attempted": repair_attempted,
                "underfilled_before_repair": underfilled_before_repair,
                "repair_succeeded_ids": repair_succeeded_ids,
                "missing_after_repair": missing_after_repair,
                "session_id": session_id,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[TestCaseGeneration] Unified generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/generate-test-cases")
async def generate_test_cases_for_scenarios(request: Request):
    """Backward-compatible UI route using the shared generation entry point."""
    from services.test_case_generation_service import TestCaseGenerationService

    return await TestCaseGenerationService().generate(await request.json())
