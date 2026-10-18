"""
test_reporting_router.py
------------------------
API Router for Test Reporting functionality
Handles comprehensive report generation from STLC processes
"""

import logging
import aiohttp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from services.test_reporting_service import test_reporting_service
from services.report_quality_evaluator import report_quality_evaluator
from utils.model_client import LLMClient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/test-reporting",
    tags=["test-reporting"]
)


def _safe_get_report_length(session: dict) -> int:
    """Safely get report content length with None checks"""
    try:
        processes = session.get("processes", {})
        if not processes or not isinstance(processes, dict):
            return 0
        
        test_reporting = processes.get("test_reporting", {})
        if not test_reporting or not isinstance(test_reporting, dict):
            return 0
        
        output = test_reporting.get("output", {})
        if not output or not isinstance(output, dict):
            return 0
        
        report_content = output.get("report_content", "")
        if not report_content or not isinstance(report_content, str):
            return 0
        
        return len(report_content)
    except Exception as e:
        logger.warning(f"Error getting report length: {e}")
        return 0


class SessionListRequest(BaseModel):
    """Request model for fetching available sessions"""
    process_names: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class SessionListResponse(BaseModel):
    """Response model for session list"""
    success: bool
    sessions: List[Dict[str, Any]]
    total_count: int


class ReportGenerationRequest(BaseModel):
    """Request model for generating a comprehensive report"""
    session_ids: List[str]  # Changed from session_id to session_ids for multiple sessions
    model: str  # e.g., "llama3.2:1b", "gemini-2.5-pro"
    api_key: Optional[str] = None  # Required for Gemini
    analysis_depth: str = "detailed"  # "summary" | "detailed" | "deep"
    custom_prompt: Optional[str] = None  # Optional custom prompt override


class ReportGenerationResponse(BaseModel):
    """Response model for report generation"""
    success: bool
    report_content: Optional[str] = None
    report_id: Optional[str] = None
    session_id: Optional[str] = None  # New session_id for the test reporting session
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessDataRequest(BaseModel):
    """Request model for fetching process data"""
    session_id: str
    process_name: str


class ProcessDataResponse(BaseModel):
    """Response model for process data"""
    success: bool
    process_name: str
    data: Optional[Dict[str, Any]] = None
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


async def call_llm(
    prompt: str,
    model: str,
    api_key: Optional[str] = None,
    max_tokens: int = 4000
) -> str:
    """
    Call LLM service using LLMClient (supports both LM Studio and Gemini)
    
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
        
        # Initialize LLMClient with test_reporting use_case
        llm_client = LLMClient(
            model_name=model,
            api_key=api_key,
            use_case='test_reporting'
        )
        
        # Generate response using unified LLMClient
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


@router.post("/sessions", response_model=SessionListResponse)
async def get_available_sessions(request: SessionListRequest):
    """
    Fetch available sessions with process data
    
    Returns list of sessions with process counts (excludes test reporting sessions by default)
    """
    try:
        # By default, exclude test reporting sessions from the list
        # (they are generated reports, not source data sessions)
        sessions = await test_reporting_service.fetch_available_sessions(
            process_names=request.process_names,
            date_from=request.date_from,
            date_to=request.date_to,
            include_test_reports=False  # Exclude test reporting sessions
        )
        
        return SessionListResponse(
            success=True,
            sessions=sessions,
            total_count=len(sessions) if sessions and isinstance(sessions, list) else 0
        )
    
    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/test-reports")
async def get_test_report_sessions(request: SessionListRequest):
    """
    Get all test reporting sessions (generated reports)
    These are the actual generated reports stored as independent sessions
    """
    try:
        await test_reporting_service.initialize()
        collection = test_reporting_service.db["session_history"]
        
        # Build query for test reporting sessions only
        query = {"session_type": "test_reporting"}
        
        # Date filter
        if request.date_from or request.date_to:
            query["created_at"] = {}
            if request.date_from:
                query["created_at"]["$gte"] = request.date_from
            if request.date_to:
                query["created_at"]["$lte"] = request.date_to
        
        # Fetch test reporting sessions
        cursor = collection.find(query).sort("created_at", -1)
        sessions = await cursor.to_list(length=None)
        
        # Format for response
        formatted_sessions = []
        for session in sessions:
            session_id = session.get("session_id", str(session.get("_id")))
            metadata = session.get("reporting_metadata", {})
            
            formatted_sessions.append({
                "session_id": session_id,
                "process_name": session.get("process_name", "Test Report"),
                "timestamp": session.get("created_at", ""),
                "session_type": "test_reporting",
                "model_used": metadata.get("model_used", "Unknown"),
                "analysis_depth": metadata.get("analysis_depth", "detailed"),
                "analyzed_sessions": metadata.get("analyzed_session_ids", []),
                "session_count": metadata.get("session_count", 0),
                "report_length": _safe_get_report_length(session),
                "processes": session.get("processes", {})
            })
        
        return SessionListResponse(
            success=True,
            sessions=formatted_sessions,
            total_count=len(formatted_sessions) if formatted_sessions and isinstance(formatted_sessions, list) else 0
        )
    
    except Exception as e:
        logger.error(f"Error fetching test report sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview-prompt")
async def preview_prompt(request: ReportGenerationRequest):
    """
    Preview the prompt that will be used for report generation
    Allows users to review and edit before generating
    """
    try:
        # Fetch session data
        session_data_list = []
        for session_id in request.session_ids:
            session = await test_reporting_service.fetch_session_data(session_id)
            if session:
                session_data_list.append(session)
        
        if not session_data_list:
            raise HTTPException(status_code=404, detail="No valid sessions found")
        
        # Generate prompt preview
        session_ids = request.session_ids if request.session_ids else []
        is_multi_session = len(session_ids) > 1 if session_ids and isinstance(session_ids, list) else False
        
        if is_multi_session:
            # Multi-session comparison
            prompt = await test_reporting_service.create_final_synthesis_prompt(
                intermediate_summaries=[],  # Empty for preview
                session_metadata={
                    "session_ids": session_ids,
                    "comparison_mode": True,
                    "session_count": len(session_ids)
                },
                analysis_depth=request.analysis_depth,
                raw_session_data=session_data_list
            )
        else:
            # Single session
            prompt = test_reporting_service.create_single_session_prompt(
                session_data=session_data_list[0],
                analysis_depth=request.analysis_depth
            )
        
        return {
            "success": True,
            "prompt": prompt,
            "session_count": len(session_ids) if session_ids and isinstance(session_ids, list) else 0,
            "analysis_depth": request.analysis_depth,
            "prompt_length": len(prompt) if prompt else 0,
            "estimated_tokens": len(prompt) // 4 if prompt else 0  # Rough estimate
        }
    
    except Exception as e:
        logger.error(f"Error generating prompt preview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-report", response_model=ReportGenerationResponse)
async def generate_comprehensive_report(request: ReportGenerationRequest):
    """
    Generate comprehensive test report from selected processes across multiple sessions
    
    This endpoint:
    1. Fetches session data for all selected sessions and processes
    2. Creates smart chunks from each process in each session
    3. Generates intermediate summaries via LLM
    4. Synthesizes final comprehensive comparison report
    5. Saves report to database
    """
    try:
        # Validate session_ids
        if not request.session_ids or not isinstance(request.session_ids, list):
            raise HTTPException(status_code=400, detail="session_ids must be a non-empty list")
        
        session_count = len(request.session_ids) if isinstance(request.session_ids, list) else 0
        logger.info(f"Starting report generation for {session_count} sessions")
        logger.info(f"Sessions: {request.session_ids}")
        logger.info(f"Model: {request.model}, Analysis depth: {request.analysis_depth}")
        
        # Step 1: Fetch session data for all sessions (all processes)
        all_session_data = []
        for session_id in request.session_ids:
            session_data = await test_reporting_service.fetch_session_data(
                session_id=session_id,
                selected_processes=None  # Fetch all processes for this session
            )
            
            processes = session_data.get('processes', {})
            process_count = len(processes) if processes and isinstance(processes, dict) else 0
            process_names = list(processes.keys()) if processes and isinstance(processes, dict) else []
            
            logger.info(f"Fetched session {session_id}: {process_count} processes")
            logger.info(f"Process names: {process_names}")
            
            if processes:
                all_session_data.append({
                    "session_id": session_id,
                    "data": session_data
                })
            else:
                logger.warning(f"No processes found for session {session_id}")
        
        # Safety check for session data
        if not all_session_data:
            raise ValueError("No process data found for selected sessions and processes")
        
        logger.info(f"Total sessions with data: {len(all_session_data) if all_session_data else 0}")
        
        # Step 2: Create chunks and generate intermediate summaries
        intermediate_summaries = []
        total_chunks = 0
        processed_chunks = 0
        
        for session_info in all_session_data:
            session_id = session_info["session_id"]
            session_data = session_info["data"]
            
            for process_name, process_data in session_data["processes"].items():
                # Create chunks for this process
                try:
                    chunks = test_reporting_service.create_chunks(process_name, process_data)
                    if not chunks or not isinstance(chunks, list):
                        logger.warning(f"No chunks created for {process_name}")
                        continue
                except Exception as e:
                    logger.error(f"Error creating chunks for {process_name}: {e}")
                    continue
                    
                total_chunks += len(chunks)
                
                logger.info(f"Processing {len(chunks)} chunks for {process_name} in session {session_id}")
                
                # Process each chunk
                for chunk in chunks:
                    # Create intermediate prompt
                    prompt = test_reporting_service.create_intermediate_prompt(
                        chunk=chunk,
                        analysis_depth=request.analysis_depth
                    )
                    
                    # Call LLM for intermediate summary
                    logger.info(f"Analyzing chunk {chunk['chunk_index'] + 1}/{len(chunks)} of {process_name} (Session: {session_id})")
                    
                    summary = await call_llm(
                        prompt=prompt,
                        model=request.model,
                        api_key=request.api_key,
                        max_tokens=2000  # Intermediate summaries can be shorter
                    )
                    
                    # Only add if summary is not empty
                    if summary and summary.strip():
                        intermediate_summaries.append({
                            "session_id": session_id,
                            "process_name": process_name,
                            "chunk_index": chunk["chunk_index"],
                            "total_chunks": chunk["total_chunks"],
                            "summary": summary
                        })
                    else:
                        logger.warning(f"Empty summary received for {process_name} chunk {chunk['chunk_index'] + 1}")
                    
                    processed_chunks += 1
                    logger.info(f"Progress: {processed_chunks}/{total_chunks} chunks processed")
        
        # Step 3: Generate final synthesis for multiple session comparison
        logger.info("Generating final synthesis report for multiple sessions...")
        
        # Safety check for intermediate summaries
        if not intermediate_summaries:
            logger.warning("No intermediate summaries generated! Generating direct report from raw data...")
            intermediate_summaries = []
        
        logger.info(f"Total intermediate summaries: {len(intermediate_summaries)}")
        
        # Prepare session metadata for all sessions
        sessions_metadata = []
        if all_session_data and isinstance(all_session_data, list):
            for session_info in all_session_data:
                if not session_info or not isinstance(session_info, dict):
                    continue
                session_data = session_info.get("data", {})
                if not session_data:
                    continue
                sessions_metadata.append({
                    "session_id": session_info.get("session_id", ""),
                    "session_timestamp": session_data.get("session_timestamp", "") or "",
                    "process_name": session_data.get("process_name", "") or ""
                })
        
        logger.info(f"Sessions metadata prepared: {len(sessions_metadata)} sessions")
        
        # Use custom prompt if provided, otherwise generate default prompt
        if request.custom_prompt:
            final_prompt = request.custom_prompt
            logger.info("Using custom user-provided prompt")
        else:
            # Safe check for comparison mode
            session_ids = request.session_ids if request.session_ids else []
            is_comparison = len(session_ids) > 1 if session_ids and isinstance(session_ids, list) else False
            
            final_prompt = await test_reporting_service.create_final_synthesis_prompt(
                intermediate_summaries=intermediate_summaries,
                session_metadata={
                    "session_ids": session_ids,
                    "sessions": sessions_metadata,
                    "comparison_mode": is_comparison
                },
                analysis_depth=request.analysis_depth,
                raw_session_data=all_session_data  # Pass raw data for LLM reference
            )
        
        # Safety check for final_prompt
        if final_prompt is None:
            raise ValueError("Failed to generate final prompt - returned None")
        
        prompt_length = len(final_prompt) if isinstance(final_prompt, str) else 0
        logger.info(f"Final prompt length: {prompt_length} characters")
        if not request.custom_prompt:
            data_count = len(all_session_data) if all_session_data and isinstance(all_session_data, list) else 0
            logger.info(f"Prompt contains {data_count} raw session data entries")
        
        # Call LLM for final report
        logger.info(f"Calling LLM with model: {request.model}")
        final_report = await call_llm(
            prompt=final_prompt,
            model=request.model,
            api_key=request.api_key,
            max_tokens=8000  # Set to Gemini's max output limit (8192)
        )
        
        # Clean up markdown code blocks if present
        cleaned_report = final_report.strip()
        
        # Remove JSON wrappers if LLM returned JSON instead of markdown
        if cleaned_report.startswith('{') and cleaned_report.endswith('}'):
            try:
                import json
                json_response = json.loads(cleaned_report)
                # Try to extract markdown from common JSON fields
                if 'full_report_markdown' in json_response:
                    cleaned_report = json_response['full_report_markdown']
                elif 'report_content' in json_response:
                    cleaned_report = json_response['report_content']
                elif 'markdown' in json_response:
                    cleaned_report = json_response['markdown']
                elif 'sections' in json_response:
                    # If JSON has sections, convert to markdown with proper headers
                    logger.warning("LLM returned JSON format instead of markdown. Converting sections to markdown...")
                    markdown_parts = []
                    sections = json_response.get('sections', {})
                    
                    for section_key, section_data in sections.items():
                        if isinstance(section_data, dict):
                            # Extract title, icon, and content
                            title = section_data.get('title', section_key.replace('_', ' ').title())
                            icon = section_data.get('icon', '📋')
                            content = section_data.get('content', '')
                            
                            # Remove duplicate header from content if present
                            # Content often starts with: # 📋 TEST SUMMARY
                            content_lines = content.split('\n')
                            if content_lines and content_lines[0].strip().startswith('#'):
                                # Remove first line if it's a header (duplicate)
                                content = '\n'.join(content_lines[1:]).strip()
                            
                            # Create markdown section with proper header
                            section_md = f"## {icon} {title}\n\n{content}"
                            markdown_parts.append(section_md)
                    
                    cleaned_report = '\n\n'.join(markdown_parts)
                    logger.info(f"✅ Converted {len(markdown_parts)} JSON sections to markdown format")
            except json.JSONDecodeError:
                logger.warning("⚠️ Failed to parse JSON response, using original text")
                pass  # Not JSON, continue with original
        
        # Remove markdown code block wrappers
        if cleaned_report.startswith('```'):
            # Remove markdown code block wrappers
            lines = cleaned_report.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]  # Remove first ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]  # Remove last ```
            cleaned_report = '\n'.join(lines).strip()
        
        final_report = cleaned_report
        report_format = "markdown"  # Simple markdown format
        logger.info("✅ Generated ISTQB/IEEE compliant markdown report")
        
        # Step 3.5: Evaluate report quality using methodology-compliant evaluator
        logger.info("📊 Evaluating report quality using deterministic methodology...")
        
        # Prepare execution data from session data for coverage calculation
        execution_data = {}
        if all_session_data and len(all_session_data) > 0:
            first_session = all_session_data[0]
            if first_session and isinstance(first_session, dict):
                processes = first_session.get("processes", {})
                if isinstance(processes, dict):
                    # Extract test cases and scenarios for coverage calculation
                    for process_name, process_data in processes.items():
                        output = process_data.get("output", {})
                        if "test_cases" in output or "test_scenarios" in output:
                            if "test_cases" not in execution_data:
                                execution_data = {}
                            execution_data.update({
                                "test_cases": output.get("test_cases", []),
                                "test_scenarios": output.get("test_scenarios", {}).get("TestScenarios", [])
                            })
        
        # Step 3.5: Prepare metadata before evaluation
        # Collect all unique process names from intermediate summaries
        processes_included = list(set(
            summary["process_name"] for summary in intermediate_summaries
        ))
        
        report_metadata = {
            "session_ids": request.session_ids,
            "sessions_analyzed": len(request.session_ids),
            "processes_included": processes_included,
            "model": request.model,
            "model_used": request.model,
            "analysis_depth": request.analysis_depth,
            "total_chunks": total_chunks,
            "intermediate_summaries": len(intermediate_summaries),
            "process_names": processes_included,
            "timestamp": datetime.now().isoformat(),
            "report_format": report_format,
            "report_type": "test_reporting"
        }
        
        # Evaluate report quality using methodology-compliant evaluator
        logger.info("🔬 Evaluating report quality using deterministic methodology...")
        quality_evaluation = report_quality_evaluator.evaluate_report(
            report_content=final_report,
            execution_data=all_session_data[0] if all_session_data else None,
            metadata=report_metadata
        )
        
        logger.info(f"📊 Report Quality Evaluation:")
        logger.info(f"   Overall Score: {quality_evaluation['overall_score']:.4f}")
        logger.info(f"   - Completeness: {quality_evaluation['completeness']:.4f}")
        logger.info(f"   - Coverage: {quality_evaluation['coverage']:.4f}")
        logger.info(f"   - Clarity: {quality_evaluation['clarity']:.4f}")
        logger.info(f"   - Depth: {quality_evaluation['depth']:.4f}")
        logger.info(f"   - Consistency: {quality_evaluation['consistency']:.4f}")
        
        # Add quality evaluation to metadata
        report_metadata["quality_evaluation"] = quality_evaluation
        
        # Step 4: Save report to database
        # Metadata already prepared above with quality evaluation added
        
        # Save report as a new independent session
        new_session_id = await test_reporting_service.save_report(
            session_ids=request.session_ids,
            report_content=final_report,
            metadata=report_metadata
        )
        
        logger.info(f"✅ Report saved as new session: {new_session_id} (format: {report_format})")
        
        return ReportGenerationResponse(
            success=True,
            report_content=final_report,
            report_id=new_session_id,  # Return the new session_id as report_id
            session_id=new_session_id,  # Also return as session_id for clarity
            metadata={
                **report_metadata,
                "new_session_id": new_session_id,
                "session_type": "test_reporting"
            }
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return ReportGenerationResponse(
            success=False,
            error=str(e)
        )
    
    except HTTPException as e:
        logger.error(f"HTTP error: {str(e.detail)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return ReportGenerationResponse(
            success=False,
            error=str(e.detail)
        )
    
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return ReportGenerationResponse(
            success=False,
            error=f"Report generation failed: {str(e)}"
        )


@router.get("/process/{session_id}/{process_name}", response_model=ProcessDataResponse)
async def get_process_data(session_id: str, process_name: str):
    """
    Fetch specific process data from a session
    
    Useful for previewing process data before report generation
    """
    try:
        session_data = await test_reporting_service.fetch_session_data(
            session_id=session_id,
            selected_processes=[process_name]
        )
        
        process_data = session_data.get("processes", {}).get(process_name)
        
        if not process_data:
            raise ValueError(f"Process {process_name} not found in session {session_id}")
        
        return ProcessDataResponse(
            success=True,
            process_name=process_name,
            data=process_data
        )
    
    except ValueError as e:
        return ProcessDataResponse(
            success=False,
            process_name=process_name,
            error=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error fetching process data: {str(e)}")
        return ProcessDataResponse(
            success=False,
            process_name=process_name,
            error=str(e)
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "test-reporting",
        "timestamp": datetime.now().isoformat()
    }
