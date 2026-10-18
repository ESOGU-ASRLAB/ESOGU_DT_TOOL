"""
Test Planning prompt yönetimi için API endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any
from core.prompt_manager import (
    get_base_prompt,
    get_test_planning_system_suffix,
    save_custom_prompt
)

router = APIRouter(tags=["test_planning_prompts"])

class PromptSaveResponse(BaseModel):
    status: str
    message: str
    process_type: str

class TestPlanningPromptResponse(BaseModel):
    prompt_text: str
    system_suffix: str
    process_type: str

@router.get("/api/prompts/test-planning", response_model=TestPlanningPromptResponse)
async def get_test_planning_prompt():
    """
    Sadece test_planning için prompt ve system_suffix döndürür.
    """
    base_prompt = get_base_prompt("test_planning")
    system_suffix = get_test_planning_system_suffix()
    if base_prompt:
        return {
            "prompt_text": base_prompt,
            "system_suffix": system_suffix,
            "process_type": "test-planning"
        }
    raise HTTPException(status_code=404, detail="Prompt for test-planning not found")

@router.post("/api/prompts/test-planning", response_model=PromptSaveResponse)
async def save_test_planning_prompt(data: Dict[str, Any] = Body(...)):
    """
    Sadece test_planning için yeni base prompt ekler (admin için).
    """
    custom_prompt = data.get("prompt")
    if not custom_prompt:
        raise HTTPException(status_code=400, detail="Prompt content is required")
    result = save_custom_prompt("test_planning", custom_prompt)
    if result:
        return {
            "status": "success",
            "message": "Prompt saved successfully",
            "process_type": "test-planning"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save prompt") 