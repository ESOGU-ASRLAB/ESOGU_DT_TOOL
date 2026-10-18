"""
Environment Setup prompt yönetimi için API endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any
from core.prompt_manager import (
    get_base_prompt,
    get_environment_setup_system_suffix,
    save_custom_prompt
)

router = APIRouter(tags=["environment_setup_prompts"])

class PromptSaveResponse(BaseModel):
    status: str
    message: str
    process_type: str

class EnvironmentSetupPromptResponse(BaseModel):
    prompt_text: str
    system_suffix: str
    process_type: str

@router.get("/api/prompts/environment-setup", response_model=EnvironmentSetupPromptResponse)
async def get_environment_setup_prompt():
    """
    Sadece environment_setup için prompt ve system_suffix döndürür.
    """
    base_prompt = get_base_prompt("environment_setup")
    system_suffix = get_environment_setup_system_suffix()
    if base_prompt:
        return {
            "prompt_text": base_prompt,
            "system_suffix": system_suffix,
            "process_type": "environment-setup"
        }
    raise HTTPException(status_code=404, detail="Prompt for environment-setup not found")

@router.post("/api/prompts/environment-setup", response_model=PromptSaveResponse)
async def save_environment_setup_prompt(data: Dict[str, Any] = Body(...)):
    """
    Sadece environment_setup için yeni base prompt ekler (admin için).
    """
    custom_prompt = data.get("prompt")
    if not custom_prompt:
        raise HTTPException(status_code=400, detail="Prompt content is required")
    result = save_custom_prompt("environment_setup", custom_prompt)
    if result:
        return {
            "status": "success",
            "message": "Prompt saved successfully",
            "process_type": "environment-setup"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save prompt") 