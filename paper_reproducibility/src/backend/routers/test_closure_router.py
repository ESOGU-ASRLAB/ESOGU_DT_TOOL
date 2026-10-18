"""
test_closure_router.py
----------------------
Test Closure API Router
Handles test cycle closure report generation with AI-powered analysis
"""

import logging
import aiohttp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from services.test_closure_service import test_closure_service
from utils.model_client import LLMClient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/test-closure",
    tags=["test-closure"]
)

# LLM Service URLs
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class SessionFilterRequest(BaseModel):
    """Request model for filtering sessions"""
    session_ids: Optional[List[str]] = None
    date_from: Optional[str] = None  # ISO format: "2025-11-01"
    date_to: Optional[str] = None


class ClosureReportRequest(BaseModel):
    """Request model for generating closure report"""
    session_ids: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    model: str  # e.g., "llama3.2:3b", "gemini-2.0-flash-exp"
    api_key: Optional[str] = None  # Required for Gemini
    custom_prompt: Optional[str] = None  # Optional custom prompt override


class ClosureMetricsResponse(BaseModel):
    """Response model for closure metrics"""
    success: bool
    metrics: Optional[Dict[str, Any]] = None
    sessions_analyzed: Optional[int] = None
    error: Optional[str] = None


class ClosureReportResponse(BaseModel):
    """Response model for closure report generation"""
    success: bool
    report_content: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    sessions_analyzed: Optional[int] = None
    model_used: Optional[str] = None
    provider: Optional[str] = None
    timestamp: Optional[str] = None
    quality_evaluation: Optional[Dict[str, Any]] = None  # Report quality metrics
    session_id: Optional[str] = None  # NEW: Saved session ID
    error: Optional[str] = None


def parse_model_to_provider_info(model_key: str) -> tuple[str, str]:
    """
    Convert model key to provider and model_name
    Returns (provider, model_name)
    """
    if model_key.startswith('gemini'):
        return ("gemini", model_key)
    else:
        return ("lm_studio", model_key)


def convert_to_lm_studio_format(model_key: str) -> str:
    """
    Convert frontend model key to LM Studio model format
    
    Examples:
        llama3.2:3b -> llama-3.2-3b-instruct
        llama3.2:1b -> llama-3.2-1b-instruct
        qwen2.5:7b -> qwen2.5-7b-instruct-1m
        codegeex4:9b -> (keep as is, or map if needed)
    
    Returns the converted model name for LM Studio
    """
    # Known mappings from frontend format to LM Studio format
    model_mappings = {
        "llama3.2:3b": "llama-3.2-3b-instruct",
        "llama3.2:1b": "llama-3.2-1b-instruct",
        "qwen2.5:7b": "qwen2.5-7b-instruct-1m",
        "openai/gpt-oss-20b": "openai/gpt-oss-20b",
    }
    
    # Check if we have an exact mapping
    if model_key in model_mappings:
        return model_mappings[model_key]
    
    # Try to auto-convert common patterns
    # Pattern: modelname:size -> modelname-size-instruct
    if ":" in model_key:
        parts = model_key.split(":")
        if len(parts) == 2:
            base_name = parts[0].replace(".", "-")  # llama3.2 -> llama-3-2
            size = parts[1]  # 3b
            # Try common patterns
            converted = f"{base_name}-{size}-instruct"
            logger.info(f"[convert_to_lm_studio_format] Auto-converted '{model_key}' -> '{converted}'")
            return converted
    
    # If no conversion needed, return as is
    logger.info(f"[convert_to_lm_studio_format] No conversion for '{model_key}', using as is")
    return model_key


async def call_llm(
    prompt: str,
    model: str,
    api_key: Optional[str] = None,
    max_tokens: int = 8000
) -> str:
    """
    Call LLM service using LLMClient (supports both LM Studio and Gemini)
    Now with automatic chunking support for context overflow
    
    Args:
        prompt: Prompt to send
        model: Model identifier
        api_key: API key for Gemini
        max_tokens: Max tokens to generate
        
    Returns:
        LLM response text
    """
    try:
        logger.info(f"[call_llm] Initializing LLMClient with model: {model}")
        logger.info(f"[call_llm] API key provided: {'Yes' if api_key else 'No'}")
        logger.info(f"[call_llm] Prompt length: {len(prompt)} characters")
        logger.info(f"[call_llm] Max tokens: {max_tokens}")
        
        # Initialize LLMClient with test_closure use_case
        llm_client = LLMClient(
            model_name=model,
            api_key=api_key,
            use_case='test_closure'
        )
        
        # Generate response using unified LLMClient (with automatic chunking)
        response = await llm_client.generate_response(
            prompt=prompt,
            temperature=0.7,
            max_tokens=max_tokens
        )
        
        if not response:
            raise ValueError("Empty response from LLM")
        
        logger.info(f"[call_llm] ✅ Successfully received response (length: {len(response)})")
        return response
        
    except Exception as e:
        error_msg = f"LLM error: {type(e).__name__}: {str(e)}"
        logger.error(f"[call_llm] ❌ Error: {error_msg}")
        logger.error(f"[call_llm] Model: {model}")
        logger.error(f"[call_llm] Prompt length: {len(prompt)} characters")
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/metrics", response_model=ClosureMetricsResponse)
async def get_closure_metrics(request: SessionFilterRequest):
    """
    Calculate test closure metrics without AI report generation
    
    Returns aggregated metrics from specified sessions
    """
    try:
        logger.info(f"[TestClosure] Calculating metrics for sessions: {request.session_ids}")
        
        result = await test_closure_service.generate_closure_report(
            session_ids=request.session_ids,
            date_from=request.date_from,
            date_to=request.date_to
        )
        
        if not result["success"]:
            return ClosureMetricsResponse(
                success=False,
                error=result.get("error", "Failed to calculate metrics")
            )
        
        return ClosureMetricsResponse(
            success=True,
            metrics=result["metrics"],
            sessions_analyzed=result["sessions_analyzed"]
        )
        
    except Exception as e:
        logger.error(f"Error calculating closure metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate metrics: {str(e)}"
        )


@router.post("/preview-prompt")
async def preview_closure_prompt(request: SessionFilterRequest):
    """
    Preview the AI prompt that would be generated for test closure report
    WITHOUT actually calling the LLM or generating the report
    
    This allows users to:
    - See what prompt will be used
    - Edit the prompt before generating the report
    - Understand what data will be analyzed
    
    Returns the generated prompt, metrics summary, and metadata
    """
    try:
        logger.info(f"[TestClosure] Previewing prompt for sessions: {request.session_ids}")
        
        # Generate metrics and prompt
        result = await test_closure_service.generate_closure_report(
            session_ids=request.session_ids,
            date_from=request.date_from,
            date_to=request.date_to
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to generate prompt preview")
            )
        
        prompt = result["prompt"]
        metrics = result["metrics"]
        
        # Calculate prompt statistics
        prompt_length = len(prompt)
        estimated_tokens = prompt_length // 4  # Rough estimation: 1 token ≈ 4 characters
        
        # Check if chunking was used
        uses_chunking = test_closure_service._should_chunk_data(metrics)
        
        return {
            "success": True,
            "prompt": prompt,
            "sessions_analyzed": result["sessions_analyzed"],
            "prompt_length": prompt_length,
            "estimated_tokens": estimated_tokens,
            "uses_chunking": uses_chunking,
            "metrics_summary": {
                "total_sessions": metrics["total_sessions"],
                "test_scenarios": metrics["test_scenarios"]["total"],
                "test_cases": metrics["test_cases"]["total_generated"],
                "test_execution": metrics["test_execution"]["total_executed"],
                "pass_rate": metrics["test_execution"]["pass_rate"],
                "defects": metrics["defects"]["total"]
            },
            "message": "Prompt preview generated successfully. You can edit this prompt before generating the report."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing closure prompt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to preview prompt: {str(e)}"
        )


@router.post("/generate-report", response_model=ClosureReportResponse)
async def generate_closure_report(request: ClosureReportRequest):
    """
    Generate AI-powered test closure report
    
    Supports custom prompt override for user-edited prompts
    
    Steps:
    1. Aggregate metrics from sessions (if custom_prompt not provided)
    2. Use custom_prompt OR generate AI prompt with metrics
    3. Call LLM to generate comprehensive report
    4. Return report with metadata
    """
    try:
        logger.info(f"[TestClosure] Generating report for sessions: {request.session_ids}")
        logger.info(f"[TestClosure] Using model: {request.model}")
        logger.info(f"[TestClosure] Custom prompt provided: {bool(request.custom_prompt)}")
        
        # Initialize result variable
        result = None
        
        # Determine which prompt to use
        if request.custom_prompt:
            # User provided custom edited prompt
            prompt = request.custom_prompt
            metrics = None  # Metrics not needed when using custom prompt
            logger.info(f"[TestClosure] Using custom prompt (length: {len(prompt)} characters)")
        else:
            # Generate default prompt with metrics
            result = await test_closure_service.generate_closure_report(
                session_ids=request.session_ids,
                date_from=request.date_from,
                date_to=request.date_to
            )
            
            if not result["success"]:
                return ClosureReportResponse(
                    success=False,
                    error=result.get("error", "Failed to generate closure data")
                )
            
            metrics = result["metrics"]
            prompt = result["prompt"]
            logger.info(f"[TestClosure] Using generated prompt (length: {len(prompt)} characters)")
        
        logger.info(f"[TestClosure] Calling LLM with prompt...")
        
        # Parse model to get provider and model_name
        provider, model_name = parse_model_to_provider_info(request.model)
        logger.info(f"[TestClosure] Parsed - Provider: {provider}, Model: {model_name}")
        
        # Step 2: Call LLM to generate report
        report_content = await call_llm(
            prompt=prompt,
            model=request.model,
            api_key=request.api_key,
            max_tokens=8000  # Large token limit for comprehensive report
        )
        
        logger.info(f"[TestClosure] Report generated successfully")
        logger.info(f"[TestClosure] Report length: {len(report_content)} characters")
        
        # Step 3: Evaluate report quality (SAME as Test Reporting)
        logger.info(f"[TestClosure] Evaluating closure report quality using deterministic methodology...")
        
        # Get all_session_data from result (added in generate_closure_report)
        all_session_data = result.get("all_session_data", [])
        
        quality_evaluation = test_closure_service.evaluate_closure_report_quality(
            report_content=report_content,
            metrics=metrics,
            all_session_data=all_session_data  # Pass session data like Test Reporting does
        )
        logger.info(
            f"[TestClosure] Quality Score: {quality_evaluation['overall_score']:.4f} | "
            f"Completeness: {quality_evaluation['completeness']:.4f} | "
            f"Coverage: {quality_evaluation['coverage']:.4f} | "
            f"Clarity: {quality_evaluation['clarity']:.4f} | "
            f"Depth: {quality_evaluation['depth']:.4f} | "
            f"Consistency: {quality_evaluation['consistency']:.4f}"
        )
        
        # Step 4: Save to database as new independent session
        logger.info(f"[TestClosure] Saving closure report to database...")
        
        # Prepare metadata for database save
        save_metadata = {
            "model_used": model_name,
            "provider": provider,
            "sessions_analyzed": result.get("sessions_analyzed", 0) if result else 0,
            "metrics": metrics,
            "date_from": request.date_from,
            "date_to": request.date_to,
            "generation_time": 0  # Could add timing logic if needed
        }
        
        # Add test metrics summary if available
        if metrics:
            test_execution = metrics.get("test_execution", {})
            save_metadata.update({
                "total_test_scenarios": metrics.get("test_scenarios", {}).get("total", 0),
                "total_test_cases": metrics.get("test_cases", {}).get("total_generated", 0),
                "total_test_execution": test_execution.get("total_executed", 0),
                "pass_rate": test_execution.get("pass_rate", 0)
            })
        
        # Save to database
        saved_session_id = await test_closure_service.save_closure_report_to_database(
            session_ids=request.session_ids or [],
            report_content=report_content,
            quality_evaluation=quality_evaluation,
            metadata=save_metadata
        )
        
        logger.info(f"[TestClosure] Report saved with session ID: {saved_session_id}")
        
        # Step 5: Return response with quality metrics and session ID
        return ClosureReportResponse(
            success=True,
            report_content=report_content,
            metrics=metrics,
            sessions_analyzed=result.get("sessions_analyzed", 0) if result else 0,
            model_used=model_name,
            provider=provider,
            timestamp=datetime.now().isoformat(),
            quality_evaluation=quality_evaluation,
            session_id=saved_session_id  # NEW: Include saved session ID
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating closure report: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate closure report: {str(e)}"
        )


@router.get("/available-sessions")
async def get_available_sessions(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """
    Get list of available sessions for closure analysis
    
    Query params:
        date_from: Start date (ISO format)
        date_to: End date (ISO format)
    """
    try:
        sessions = await test_closure_service.fetch_sessions_for_closure(
            date_from=date_from,
            date_to=date_to
        )
        
        # Format sessions for frontend
        session_list = []
        for session in sessions:
            processes = session.get("processes", {})
            process_names = list(processes.keys())
            
            # Support both timestamp and created_at fields for consistency
            session_timestamp = session.get("timestamp") or session.get("created_at")
            
            session_list.append({
                "session_id": session.get("session_id"),
                "timestamp": session_timestamp,  # Primary field
                "created_at": session_timestamp,  # Fallback for compatibility
                "process_count": len(process_names),
                "processes": process_names
            })
        
        return {
            "success": True,
            "sessions": session_list,
            "total_count": len(session_list)
        }
        
    except Exception as e:
        logger.error(f"Error fetching available sessions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch sessions: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "test-closure",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/lm-studio/models")
async def get_lm_studio_models():
    """Get available models from LM Studio"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:1234/v1/models", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    return {
                        "success": True,
                        "models": models,
                        "count": len(models)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"LM Studio returned status {response.status}"
                    }
    except Exception as e:
        return {
            "success": False,
            "error": f"Could not connect to LM Studio: {str(e)}"
        }
