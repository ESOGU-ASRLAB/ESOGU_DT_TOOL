"""
Requirement Analysis prompt yönetimi için API endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any
from core.prompt_manager import (
    get_base_prompt,
    get_requirement_analysis_system_suffix,
    save_custom_prompt
)

router = APIRouter(tags=["requirement_analysis_prompts"])

class PromptSaveResponse(BaseModel):
    status: str
    message: str
    process_type: str

class RequirementAnalysisPromptResponse(BaseModel):
    prompt_text: str
    system_suffix: str  
    process_type: str

@router.get("/api/prompts/requirement-analysis", response_model=RequirementAnalysisPromptResponse)
async def get_requirement_analysis_prompt():
    """
    Sadece requirement_analysis için prompt ve system_suffix döndürür.
    """
    base_prompt = get_base_prompt("requirement_analysis")
    system_suffix = get_requirement_analysis_system_suffix()
    if base_prompt:
        return {
            "prompt_text": base_prompt,
            "system_suffix": system_suffix,
            "process_type": "requirement-analysis"
        }
    raise HTTPException(status_code=404, detail="Prompt for requirement-analysis not found")

@router.post("/api/prompts/requirement-analysis", response_model=PromptSaveResponse)
async def save_requirement_analysis_prompt(data: Dict[str, Any] = Body(...)):
    """
    Sadece requirement_analysis için yeni base prompt ekler (admin için).
    """
    custom_prompt = data.get("prompt")
    if not custom_prompt:
        raise HTTPException(status_code=400, detail="Prompt content is required")
    result = save_custom_prompt("requirement_analysis", custom_prompt)
    if result:
        return {
            "status": "success",
            "message": "Prompt saved successfully",
            "process_type": "requirement-analysis"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save prompt") 