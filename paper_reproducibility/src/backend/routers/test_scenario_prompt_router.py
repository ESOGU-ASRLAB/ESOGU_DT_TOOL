"""
Test Scenario Generation ve Test Case Generation prompt yönetimi için API endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from core.prompt_manager import (
    get_base_prompt,
    save_custom_prompt
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["test_scenario_prompts"])

class PromptSaveResponse(BaseModel):
    status: str
    message: str
    process_type: str

class PromptResponse(BaseModel):
    prompt_text: str
    process_type: str
    status: str

@router.get("/api/prompts/test-scenario-generation", response_model=PromptResponse)
async def get_test_scenario_generation_prompt():
    """
    Test Scenario Generation için prompt döndürür.
    """
    try:
        base_prompt = get_base_prompt("test_scenario_generation")
        
        if base_prompt:
            return {
                "prompt_text": base_prompt,
                "process_type": "test-scenario-generation",
                "status": "success"
            }
        
        # Eğer prompt bulunamazsa, default prompt döndür
        default_prompt = """Acting as a senior ISTQB-certified test analyst, generate a comprehensive set of test scenarios for the given code/requirements.

Your task is to:
1. Analyze the provided code/requirements thoroughly
2. Identify key functionalities and business logic
3. Generate test scenarios covering various testing aspects
4. Ensure comprehensive test coverage

Focus on:
- Functional testing scenarios
- Boundary value testing
- Error handling scenarios
- Integration testing aspects
- Performance considerations
- Security aspects where applicable

Provide detailed, actionable test scenarios that can be used to validate the application thoroughly."""

        return {
            "prompt_text": default_prompt,
            "process_type": "test-scenario-generation",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting test scenario generation prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/prompts/test-scenario-generation", response_model=PromptSaveResponse)
async def save_test_scenario_generation_prompt(request: Request):
    """
    Test Scenario Generation için custom prompt kaydeder.
    """
    try:
        data = await request.json()
        custom_prompt = data.get("prompt")
        
        if not custom_prompt:
            raise HTTPException(status_code=400, detail="Prompt content is required")
        
        result = save_custom_prompt("test_scenario_generation", custom_prompt)
        
        if result:
            return {
                "status": "success",
                "message": "Test scenario generation prompt saved successfully",
                "process_type": "test-scenario-generation"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save prompt")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving test scenario generation prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/prompts/test-case-generation", response_model=PromptResponse)
async def get_test_case_generation_prompt():
    """
    Test Case Generation için prompt döndürür.
    """
    try:
        base_prompt = get_base_prompt("test_case_generation")
        
        if base_prompt:
            return {
                "prompt_text": base_prompt,
                "process_type": "test-case-generation",
                "status": "success"
            }
        
        # Eğer prompt bulunamazsa, default prompt döndür
        default_prompt = """Acting as a senior ISTQB-certified test analyst, generate a comprehensive set of functional test cases for the given test scenario.

Your task is to:
1. Analyze the provided test scenario thoroughly
2. Create detailed test cases that validate all aspects of the scenario
3. Include both positive and negative test cases
4. Cover edge cases and boundary conditions
5. Ensure each test case is actionable and specific

Each test case should include:
- Test Case ID
- Title
- Description
- Objective
- Category

Focus on creating test cases that are:
- Clear and unambiguous
- Executable by any tester
- Comprehensive in coverage
- Properly categorized
- Include proper validation points"""

        return {
            "prompt_text": default_prompt,
            "process_type": "test-case-generation",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting test case generation prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/prompts/test-case-generation", response_model=PromptSaveResponse)
async def save_test_case_generation_prompt(request: Request):
    """
    Test Case Generation için custom prompt kaydeder.
    """
    try:
        data = await request.json()
        custom_prompt = data.get("prompt")
        
        if not custom_prompt:
            raise HTTPException(status_code=400, detail="Prompt content is required")
        
        result = save_custom_prompt("test_case_generation", custom_prompt)
        
        if result:
            return {
                "status": "success",
                "message": "Test case generation prompt saved successfully",
                "process_type": "test-case-generation"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save prompt")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving test case generation prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
