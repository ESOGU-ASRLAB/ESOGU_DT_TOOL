from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from services.review_service import ReviewService
import logging
from typing import Optional, List

router = APIRouter()
logger = logging.getLogger("code_review")
review_service = ReviewService()

@router.post("/run")
async def process_code_review(
    files: List[UploadFile] = File(...),
    types: Optional[List[str]] = Form(None),
    model: Optional[str] = Form(None),
    custom_prompt: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),  # session_id parametresi eklendi
    api_key: Optional[str] = Form(None)  # API key parametresi eklendi
):
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded.")
        
        logger.info(f"Code review requested with model: {model} ve session_id: {session_id}")
        # session_id parametresini de geçiriyoruz
        results = await review_service.run_code_review(files, types, model, custom_prompt, session_id, api_key)
        return results
    except Exception as e:
        logger.error(f"Code Review Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))