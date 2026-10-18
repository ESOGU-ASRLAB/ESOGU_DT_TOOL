"""
Debug specific session with test_case_generation
"""
import asyncio
from services.test_reporting_service import TestReportingService
from services.quality_metrics_calculator import quality_calculator
import json

async def debug_test_case_session():
    # Use session ID we found: 16f91ead-b607-43e2-96a2-a74d0d4a3543
    session_id = "16f91ead-b607-43e2-96a2-a74d0d4a3543"
    
    service = TestReportingService()
    await service.initialize()
    
    # Fetch session data
    session_data = await service.fetch_session_data(session_id)
    
    print("=" * 70)
    print(f"Session: {session_id}")
    print("=" * 70)
    
    if "test_case_generation" in session_data["processes"]:
        tc_gen = session_data["processes"]["test_case_generation"]
        output = tc_gen.get("output", {})
        
        print(f"\noutput keys: {list(output.keys())}")
        print(f"\ntest_case_results type: {type(output.get('test_case_results'))}")
        
        test_case_results = output.get("test_case_results", [])
        print(f"test_case_results length: {len(test_case_results)}")
        
        if len(test_case_results) > 0:
            first_result = test_case_results[0]
            print(f"\nFirst result keys: {list(first_result.keys())}")
            print(f"\nFirst result.test_cases length: {len(first_result.get('test_cases', []))}")
            
            if first_result.get("test_cases"):
                first_tc = first_result["test_cases"][0]
                print(f"\nFirst test case keys: {list(first_tc.keys())}")
                print(f"\nFirst test case sample:")
                print(json.dumps(first_tc, indent=2, default=str)[:500])
        
        # Test quality calculation
        print(f"\n{'=' * 70}")
        print("TESTING QUALITY CALCULATION")
        print(f"{'=' * 70}")
        
        quality = quality_calculator.calculate_process_quality("test_case_generation", output)
        
        print(f"\nQuality result: {json.dumps(quality, indent=2)}")
    else:
        print("❌ test_case_generation not found in session")

if __name__ == "__main__":
    import sys
    sys.path.append('.')
    asyncio.run(debug_test_case_session())
