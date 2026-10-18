from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from services.test_planning_service import TestPlanningService
import logging
from typing import Optional, List

router = APIRouter()
logger = logging.getLogger("test_planning")
test_planning_service = TestPlanningService()

@router.post("/run")
async def process_test_planning(
    files: List[UploadFile] = File(...),
    model: Optional[str] = Form(None),
    custom_prompt: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None)  # API key parametresi eklendi
):
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded.")
        logger.info(f"Test planning requested with model: {model} ve session_id: {session_id}")
        results = await test_planning_service.run_test_planning(files, model, custom_prompt, session_id, api_key)
        return results
    except Exception as e:
        logger.error(f"Test Planning Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
