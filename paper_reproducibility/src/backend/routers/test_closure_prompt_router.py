"""
test_closure_prompt_router.py
------------------------------
Test Closure prompt yönetimi için API endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any
from core.database import get_db

router = APIRouter(tags=["test_closure_prompts"])

class PromptSaveResponse(BaseModel):
    success: bool
    message: str

class TestClosurePromptResponse(BaseModel):
    prompt_text: str
    description: str

@router.get("/api/prompts/test-closure", response_model=TestClosurePromptResponse)
async def get_test_closure_prompt():
    """
    Test closure için prompt döndürür.
    """
    try:
        db = get_db()
        
        # Fetch from MongoDB
        prompt_doc = db.test_closure_prompt.find_one({"process_type": "test_closure"})
        
        if prompt_doc:
            return TestClosurePromptResponse(
                prompt_text=prompt_doc.get("prompt_text", ""),
                description=prompt_doc.get("description", "")
            )
        else:
            # Default fallback
            return TestClosurePromptResponse(
                prompt_text="""You are an ISTQB-certified Test Manager generating a comprehensive Test Closure Report aligned with international testing standards.

Generate a comprehensive Test Closure Report following the **ISO/IEC/IEEE 29119-3 Test Completion Report Template** with the following sections:

## 1. Executive Summary
- Overall test cycle completion status
- High-level test objectives achievement
- Critical success metrics
- Key findings and outcomes

## 2. Test Objectives Achievement
- Review of initial test objectives
- Achievement status for each objective
- Deviation analysis from planned vs actual

## 3. Test Metrics and Statistics
- Total test scenarios created
- Total test cases generated and executed
- Pass/fail rates and trends
- Defect metrics (total, by severity, by status)
- Code coverage and test coverage metrics
- Test effort and resource utilization

## 4. Quality Assessment
- Product quality assessment based on test results
- Risk assessment and residual risks
- Quality gates achievement status
- Areas of concern and limitations

## 5. Defect Analysis
- Defect summary by priority and severity
- Root cause analysis of critical defects
- Defect resolution status and trends
- Outstanding defects impact assessment

## 6. Test Completeness
- Test coverage analysis
- Untested areas identification
- Test exit criteria evaluation
- Test completion confidence level

## 7. Lessons Learned
- What went well during testing
- Challenges faced and how they were overcome
- Process improvements identified
- Best practices to continue

## 8. Recommendations
- Actions for future test cycles
- Process improvement suggestions
- Tool and technology recommendations
- Training and skill development needs

## 9. Test Deliverables Status
- List of test deliverables produced
- Deliverable quality assessment
- Archive and handover status

## 10. Sign-off and Approval
- Test closure recommendation
- Stakeholder sign-off requirements
- Risk acceptance statements

Session Data:
{session_data}""",
                description="Default test closure prompt following ISO/IEC/IEEE 29119-3 standards"
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/prompts/test-closure", response_model=PromptSaveResponse)
async def save_test_closure_prompt(data: Dict[str, Any] = Body(...)):
    """
    Test closure için yeni prompt ekler/günceller.
    """
    try:
        db = get_db()
        
        new_prompt = data.get("prompt_text", "").strip()
        
        if not new_prompt:
            raise ValueError("Prompt text cannot be empty")
        
        # Update or insert
        from datetime import datetime
        
        result = db.test_closure_prompt.update_one(
            {"process_type": "test_closure"},
            {
                "$set": {
                    "prompt_text": new_prompt,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
        
        if result.modified_count > 0 or result.upserted_id:
            return PromptSaveResponse(
                success=True,
                message="Test closure prompt saved successfully"
            )
        else:
            return PromptSaveResponse(
                success=False,
                message="No changes made to prompt"
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
