"""
Test Scenario Generation Analytics Router
----------------------------------------
Provides API endpoints for retrieving analytics and insights about test scenario generation
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/test-scenario-analytics",
    tags=["test-scenario-analytics"]
)

try:
    from services.test_scenario_analytics_service import test_scenario_analytics
except ImportError:
    test_scenario_analytics = None
    logger.warning("Analytics service not available")

@router.get("/session/{session_id}")
async def get_session_analytics(session_id: str):
    """Get comprehensive analytics for a specific test scenario generation session"""
    try:
        if not test_scenario_analytics:
            raise HTTPException(status_code=503, detail="Analytics service not available")
        
        analytics = test_scenario_analytics.get_session_analytics(session_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail=f"No analytics found for session: {session_id}")
        
        return {
            "status": "success",
            "session_id": session_id,
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quality-trends")
async def get_quality_trends(
    limit: int = Query(default=50, ge=1, le=100, description="Number of recent sessions to analyze")
):
    """Get quality trends over recent test scenario generation sessions"""
    try:
        if not test_scenario_analytics:
            raise HTTPException(status_code=503, detail="Analytics service not available")
        
        trends = test_scenario_analytics.get_quality_trends(limit=limit)
        
        # Calculate trend statistics
        if trends:
            quality_scores = [t.get("quality_metrics", {}).get("response_quality_score", 0) for t in trends]
            scenario_counts = [t.get("generation_analytics", {}).get("total_scenarios_generated", 0) for t in trends]
            
            trend_stats = {
                "total_sessions": len(trends),
                "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                "average_scenarios_per_session": sum(scenario_counts) / len(scenario_counts) if scenario_counts else 0,
                "highest_quality_score": max(quality_scores) if quality_scores else 0,
                "lowest_quality_score": min(quality_scores) if quality_scores else 0
            }
        else:
            trend_stats = {
                "total_sessions": 0,
                "average_quality_score": 0,
                "average_scenarios_per_session": 0,
                "highest_quality_score": 0,
                "lowest_quality_score": 0
            }
        
        return {
            "status": "success",
            "trend_statistics": trend_stats,
            "sessions": trends
        }
        
    except Exception as e:
        logger.error(f"Error retrieving quality trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-type-statistics")
async def get_test_type_statistics():
    """Get statistics grouped by test type"""
    try:
        if not test_scenario_analytics:
            raise HTTPException(status_code=503, detail="Analytics service not available")
        
        stats = test_scenario_analytics.get_test_type_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error retrieving test type statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_analytics_dashboard():
    """Get comprehensive dashboard data for test scenario generation analytics"""
    try:
        if not test_scenario_analytics:
            raise HTTPException(status_code=503, detail="Analytics service not available")
        
        # Get recent trends
        recent_trends = test_scenario_analytics.get_quality_trends(limit=30)
        
        # Get test type statistics
        test_type_stats = test_scenario_analytics.get_test_type_statistics()
        
        # Calculate overall metrics
        if recent_trends:
            total_sessions = len(recent_trends)
            total_scenarios = sum(t.get("generation_analytics", {}).get("total_scenarios_generated", 0) for t in recent_trends)
            avg_quality = sum(t.get("quality_metrics", {}).get("response_quality_score", 0) for t in recent_trends) / total_sessions
            
            # Model usage statistics
            model_usage = {}
            for trend in recent_trends:
                model = trend.get("generation_analytics", {}).get("model_used", "unknown")
                model_usage[model] = model_usage.get(model, 0) + 1
        else:
            total_sessions = 0
            total_scenarios = 0
            avg_quality = 0
            model_usage = {}
        
        dashboard_data = {
            "overview": {
                "total_sessions_last_30": total_sessions,
                "total_scenarios_generated": total_scenarios,
                "average_quality_score": round(avg_quality, 3),
                "average_scenarios_per_session": round(total_scenarios / total_sessions, 1) if total_sessions > 0 else 0
            },
            "test_type_distribution": test_type_stats.get("test_type_stats", []),
            "model_usage_distribution": [
                {"model": model, "sessions": count, "percentage": round(count/total_sessions*100, 1)}
                for model, count in model_usage.items()
            ] if total_sessions > 0 else [],
            "recent_quality_trend": [
                {
                    "session_id": t.get("session_id"),
                    "timestamp": t.get("timestamp"),
                    "quality_score": t.get("quality_metrics", {}).get("response_quality_score", 0),
                    "scenario_count": t.get("generation_analytics", {}).get("total_scenarios_generated", 0),
                    "test_type": t.get("test_metadata", {}).get("test_type", "unknown")
                }
                for t in recent_trends[-10:]  # Last 10 sessions
            ]
        }
        
        return {
            "status": "success",
            "dashboard": dashboard_data,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def analytics_health_check():
    """Check the health of the analytics service"""
    try:
        if not test_scenario_analytics:
            return {
                "status": "unavailable",
                "analytics_service": False,
                "database_connection": False,
                "message": "Analytics service not available"
            }
        
        # Test database connection by attempting to get trends
        try:
            test_scenario_analytics.get_quality_trends(limit=1)
            db_connection = True
        except Exception:
            db_connection = False
        
        return {
            "status": "healthy" if db_connection else "degraded",
            "analytics_service": True,
            "database_connection": db_connection,
            "message": "Analytics service operational" if db_connection else "Database connection issues"
        }
        
    except Exception as e:
        logger.error(f"Error in analytics health check: {e}")
        return {
            "status": "error",
            "analytics_service": False,
            "database_connection": False,
            "message": str(e)
        }
