"""
Check Test Reporting Service Test Case Counting
Verifies that test reporting correctly counts test cases
"""

import asyncio
import json
from core.database import get_database
from services.test_reporting_service import TestReportingService

async def check_test_reporting_counts():
    """
    Check if test reporting service correctly counts test cases
    """
    db = await get_database()
    collection = db["session_history"]
    
    # Find a session with test_reporting
    cursor = collection.find({"processes.test_reporting": {"$exists": True}}).limit(5)
    sessions = await cursor.to_list(length=5)
    
    if not sessions:
        print("❌ No sessions with test_reporting found")
        return
    
    print(f"\n{'='*80}")
    print(f"📊 Found {len(sessions)} sessions with test_reporting")
    print(f"{'='*80}\n")
    
    service = TestReportingService()
    
    for session in sessions:
        session_id = session.get("session_id", "unknown")
        print(f"\n{'='*80}")
        print(f"Session: {session_id}")
        print(f"{'='*80}\n")
        
        processes = session.get("processes", {})
        
        # Check what data exists in processes
        for proc_name in ["test_scenario_generation", "test_case_generation", "test_case_optimization", "test_execution"]:
            if proc_name in processes:
                proc_data = processes[proc_name]
                output = proc_data.get("output", {})
                
                # Use service's count method
                count = service._count_items_in_process(proc_name, output)
                
                print(f"✅ {proc_name}: {count} items")
                
                # For test_case_generation, show detailed breakdown
                if proc_name == "test_case_generation" and count > 0:
                    # Check which format is being used
                    test_case_results = output.get("test_case_results", [])
                    if test_case_results:
                        print(f"   📦 Format: output.test_case_results (direct)")
                        print(f"   📦 Groups: {len(test_case_results)}")
                        for i, result in enumerate(test_case_results[:3], 1):
                            scenario_id = result.get("scenario_id", "?")
                            tc_count = len(result.get("test_cases", []))
                            print(f"      {i}. Scenario {scenario_id}: {tc_count} test cases")
                        if len(test_case_results) > 3:
                            print(f"      ... and {len(test_case_results) - 3} more groups")
                    else:
                        data = output.get("data", {})
                        test_case_results = data.get("test_case_results", [])
                        if test_case_results:
                            print(f"   📦 Format: output.data.test_case_results (nested)")
                        else:
                            test_cases = output.get("test_cases", [])
                            if test_cases:
                                print(f"   📦 Format: output.test_cases (flat list)")
        
        print()

async def main():
    print("\n🔍 Testing Test Reporting Service Test Case Counting...")
    await check_test_reporting_counts()

if __name__ == "__main__":
    asyncio.run(main())
