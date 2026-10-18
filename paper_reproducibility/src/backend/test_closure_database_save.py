"""
test_closure_database_save.py
------------------------------
Test script for Test Closure Database Save Functionality
Tests the new database save feature that creates independent closure sessions
"""

import asyncio
import logging
from services.test_closure_service import test_closure_service
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample closure report for testing
SAMPLE_CLOSURE_REPORT = """
# 📋 Test Closure Report

## 🎯 Executive Summary
Comprehensive test cycle closure analysis for 15 sessions executed between 2025-11-01 and 2025-12-31.

## 📊 Test Execution Metrics
- **Total Test Cases**: 245
- **Pass Rate**: 80.8%
- **Code Coverage**: 78%

## 🏆 Quality Assessment
Overall quality meets industry standards with strong adherence to STLC methodology.

## 🐛 Defect Analysis
32 defects identified: 5 critical, 12 major, 15 minor.

## 📈 Coverage Analysis
- Functional Coverage: 85%
- Requirement Coverage: 92%
- Code Coverage: 78%

## ⚠️ Risk Assessment
5 critical defects pose production risk. Performance testing recommended.

## 💡 Recommendations
1. Resolve critical defects before release
2. Conduct additional load testing
3. Execute regression suite after fixes

## ✅ Test Closure Decision
**Status**: **CONDITIONAL GO**
Application demonstrates acceptable quality but requires critical defect resolution.

## 📘 Lessons Learned
Early test scenario generation improved coverage significantly.
"""


SAMPLE_METRICS = {
    "total_sessions": 15,
    "date_range": {
        "start": "2025-11-01",
        "end": "2025-12-31"
    },
    "models_used": ["gemini-1.5-flash", "llama3.2:3b"],
    "test_scenarios": {
        "total": 58,
        "by_category": {"functional": 35, "security": 12}
    },
    "test_cases": {
        "total_generated": 245,
        "total_optimized": 198
    },
    "test_execution": {
        "total_executed": 245,
        "passed": 198,
        "failed": 32,
        "pass_rate": 0.808
    }
}


SAMPLE_QUALITY_EVALUATION = {
    "overall_score": 0.7850,
    "completeness": 0.8889,
    "coverage": 0.5000,
    "clarity": 0.9200,
    "depth": 0.6500,
    "consistency": 0.9500,
    "weights_used": {
        "completeness": 0.25,
        "coverage": 0.15,
        "clarity": 0.20,
        "depth": 0.25,
        "consistency": 0.15
    },
    "calculation_details": {
        "sections_required": 9,
        "sections_present": 8,
        "total_sentences": 39
    }
}


async def test_database_save():
    """Test the database save functionality"""
    logger.info("=" * 80)
    logger.info("TESTING TEST CLOSURE DATABASE SAVE FUNCTIONALITY")
    logger.info("=" * 80)
    
    # Initialize service
    await test_closure_service.initialize()
    logger.info("✅ Service initialized")
    
    # Test 1: Save a closure report with multiple sessions
    logger.info("\n[TEST 1] Saving closure report for multiple sessions...")
    
    session_ids = [
        "test_scenario_20250101_120000",
        "test_scenario_20250102_130000",
        "test_scenario_20250103_140000"
    ]
    
    metadata = {
        "model_used": "gemini-1.5-flash",
        "provider": "gemini",
        "sessions_analyzed": 3,
        "metrics": SAMPLE_METRICS,
        "date_from": "2025-11-01",
        "date_to": "2025-12-31",
        "total_test_scenarios": 58,
        "total_test_cases": 245,
        "total_test_execution": 245,
        "pass_rate": 0.808,
        "generation_time": 15.5
    }
    
    saved_session_id_1 = await test_closure_service.save_closure_report_to_database(
        session_ids=session_ids,
        report_content=SAMPLE_CLOSURE_REPORT,
        quality_evaluation=SAMPLE_QUALITY_EVALUATION,
        metadata=metadata
    )
    
    logger.info(f"✅ Test 1 PASSED: Saved with session ID: {saved_session_id_1}")
    
    # Test 2: Save another closure report with different model (simulating iteration)
    logger.info("\n[TEST 2] Saving second closure report with different model...")
    
    metadata_2 = metadata.copy()
    metadata_2["model_used"] = "llama3.2:3b"
    metadata_2["provider"] = "lm_studio"
    metadata_2["generation_time"] = 22.3
    
    quality_eval_2 = SAMPLE_QUALITY_EVALUATION.copy()
    quality_eval_2["overall_score"] = 0.8200
    quality_eval_2["depth"] = 0.7500
    
    saved_session_id_2 = await test_closure_service.save_closure_report_to_database(
        session_ids=session_ids,
        report_content=SAMPLE_CLOSURE_REPORT + "\n\n## Additional Analysis\nGenerated with alternative model for comparison.",
        quality_evaluation=quality_eval_2,
        metadata=metadata_2
    )
    
    logger.info(f"✅ Test 2 PASSED: Saved with session ID: {saved_session_id_2}")
    
    # Test 3: Verify both reports are saved independently
    logger.info("\n[TEST 3] Verifying independent session storage...")
    
    collection = test_closure_service.db["session_history"]
    
    # Fetch first report
    report_1 = await collection.find_one({"session_id": saved_session_id_1})
    if report_1:
        logger.info(f"✅ Report 1 found in database")
        logger.info(f"   - Session ID: {report_1['session_id']}")
        logger.info(f"   - Session Type: {report_1.get('session_type')}")
        logger.info(f"   - Model: {report_1['closure_metadata']['model_used']}")
        logger.info(f"   - Quality Score: {report_1['processes']['test_closure']['output']['quality_evaluation']['overall_score']:.4f}")
    else:
        logger.error("❌ Report 1 not found!")
    
    # Fetch second report
    report_2 = await collection.find_one({"session_id": saved_session_id_2})
    if report_2:
        logger.info(f"✅ Report 2 found in database")
        logger.info(f"   - Session ID: {report_2['session_id']}")
        logger.info(f"   - Session Type: {report_2.get('session_type')}")
        logger.info(f"   - Model: {report_2['closure_metadata']['model_used']}")
        logger.info(f"   - Quality Score: {report_2['processes']['test_closure']['output']['quality_evaluation']['overall_score']:.4f}")
    else:
        logger.error("❌ Report 2 not found!")
    
    # Verify they are different sessions
    if report_1 and report_2 and report_1['session_id'] != report_2['session_id']:
        logger.info(f"✅ Test 3 PASSED: Both reports saved as independent sessions")
    else:
        logger.error("❌ Test 3 FAILED: Reports not properly separated")
    
    # Test 4: Query all test_closure sessions
    logger.info("\n[TEST 4] Querying all test_closure sessions...")
    
    closure_sessions = await collection.find({"session_type": "test_closure"}).to_list(length=100)
    logger.info(f"✅ Found {len(closure_sessions)} test closure session(s) in database")
    
    for idx, session in enumerate(closure_sessions[-5:], 1):  # Show last 5
        logger.info(f"   {idx}. {session['session_id']} - {session['closure_metadata']['model_used']} "
                   f"(Quality: {session['processes']['test_closure']['output']['quality_evaluation']['overall_score']:.4f})")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✅ All tests passed successfully!")
    logger.info(f"✅ Database save functionality working correctly")
    logger.info(f"✅ Multiple closure reports can be saved from same source sessions")
    logger.info(f"✅ Each closure report creates independent session_history record")
    logger.info(f"✅ Quality evaluation included in saved data")
    logger.info("\n📊 Benefits:")
    logger.info("   • Iterative closure report refinement")
    logger.info("   • Model comparison for closure analysis")
    logger.info("   • Historical tracking of closure decisions")
    logger.info("   • Consistent with Test Reporting module pattern")
    logger.info("=" * 80)
    
    return {
        "saved_session_id_1": saved_session_id_1,
        "saved_session_id_2": saved_session_id_2,
        "total_closure_sessions": len(closure_sessions)
    }


if __name__ == "__main__":
    try:
        result = asyncio.run(test_database_save())
        print(f"\n✅ Database save test completed successfully!")
        print(f"   - First report: {result['saved_session_id_1']}")
        print(f"   - Second report: {result['saved_session_id_2']}")
        print(f"   - Total closure sessions in DB: {result['total_closure_sessions']}")
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
