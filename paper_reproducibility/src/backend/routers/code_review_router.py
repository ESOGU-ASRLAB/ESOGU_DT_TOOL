"""
Code Review prompt yönetimi için API endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any
from core.prompt_manager import (
    get_base_prompt,
    get_code_review_system_suffix,
    save_custom_prompt
)

router = APIRouter(tags=["code_review_prompts"])

class PromptSaveResponse(BaseModel):
    status: str
    message: str
    process_type: str

class CodeReviewPromptResponse(BaseModel):
    prompt_text: str
    system_suffix: str
    process_type: str

@router.get("/api/prompts/code-review", response_model=CodeReviewPromptResponse)
async def get_code_review_prompt():
    """
    Sadece code_review için prompt ve system_suffix döndürür.
    """
    base_prompt = get_base_prompt("code_review")
    system_suffix = get_code_review_system_suffix()
    if base_prompt:
        return {
            "prompt_text": base_prompt,
            "system_suffix": system_suffix,
            "process_type": "code-review"
        }
    raise HTTPException(status_code=404, detail="Prompt for code-review not found")

@router.post("/api/prompts/code-review", response_model=PromptSaveResponse)
async def save_code_review_prompt(data: Dict[str, Any] = Body(...)):
    """
    Sadece code_review için yeni base prompt ekler (admin için).
    """
    custom_prompt = data.get("prompt")
    if not custom_prompt:
        raise HTTPException(status_code=400, detail="Prompt content is required")
    result = save_custom_prompt("code_review", custom_prompt)
    if result:
        return {
            "status": "success",
            "message": "Prompt saved successfully",
            "process_type": "code-review"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save prompt")