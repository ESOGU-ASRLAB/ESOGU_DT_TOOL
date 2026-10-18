"""
environment_setup.py
--------------------
STLC'nin Environment Setup adımına ait işlemleri yönetir.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from services.environment_setup_service import EnvironmentSetupService
import logging
from typing import Optional, List

router = APIRouter()
logger = logging.getLogger("environment_setup")
env_setup_service = EnvironmentSetupService()

@router.post("/run")
async def process_environment_setup(
    files: List[UploadFile] = File(...),
    types: List[str] = Form(...),
    model: Optional[str] = Form(None),
    custom_prompt: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    environment_name: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None)  # API key parametresi eklendi
):
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded.")
        logger.info(f"Environment setup requested with model: {model}, session_id: {session_id}, environment_name: {environment_name}")
        results = await env_setup_service.run_environment_setup(files, types, model, custom_prompt, session_id, environment_name, api_key)
        return results
    except Exception as e:
        logger.error(f"Environment Setup Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
