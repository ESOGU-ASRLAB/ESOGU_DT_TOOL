from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from services.requirement_analysis_service import RequirementAnalysisService
import logging
from typing import Optional, List

router = APIRouter()
logger = logging.getLogger("requirement_analysis")
requirement_analysis_service = RequirementAnalysisService()

@router.post("/run")
async def process_requirement_analysis(
    files: List[UploadFile] = File(...),
    types: Optional[List[str]] = Form(None),
    model: Optional[str] = Form(None),
    custom_prompt: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None)  # API key parametresi eklendi
):
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded.")
        logger.info(f"Requirement analysis requested with model: {model} ve session_id: {session_id}")
        results = await requirement_analysis_service.run_requirement_analysis(files, types, model, custom_prompt, session_id, api_key)
        return results
    except Exception as e:
        logger.error(f"Requirement Analysis Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))