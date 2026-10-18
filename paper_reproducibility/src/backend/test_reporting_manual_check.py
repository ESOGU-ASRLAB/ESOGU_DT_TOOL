"""
Test Reporting Service Manual Test
Simulates what test reporting service does when analyzing a session
"""

import asyncio
from core.database import get_database
from services.test_reporting_service import TestReportingService

async def test_manual_analysis():
    """Manually test the analysis like test reporting does"""
    
    service = TestReportingService()
    await service.initialize()
    
    # Analyze the specific session
    session_id = "project.xml Test Scenario&Test Cases"
    
    print(f"\n{'='*80}")
    print(f"🔍 ANALYZING SESSION: {session_id}")
    print(f"{'='*80}\n")
    
    # Get the session
    db = await get_database()
    collection = db["session_history"]
    session = await collection.find_one({"session_id": session_id})
    
    if not session:
        print("❌ Session not found")
        return
    
    processes = session.get("processes", {})
    print(f"📦 Processes in session: {list(processes.keys())}\n")
    
    # Test the count function for each process
    for process_name in ["test_scenario_generation", "test_case_generation", "test_case_optimization"]:
        if process_name in processes:
            output = processes[process_name].get("output", {})
            
            # Use the service's internal count method
            count = service._count_process_items(process_name, output)
            
            print(f"{'='*60}")
            print(f"Process: {process_name}")
            print(f"{'='*60}")
            print(f"Count: {count}")
            
            # Show detailed structure
            if process_name == "test_case_generation":
                print(f"\n🔍 Detailed Analysis:")
                
                # Check format 1: output.test_case_results
                test_case_results = output.get("test_case_results", [])
                if test_case_results:
                    print(f"   ✅ Found test_case_results at output.test_case_results")
                    print(f"   📦 Groups: {len(test_case_results)}")
                    total = sum(len(r.get("test_cases", [])) for r in test_case_results)
                    print(f"   📊 Total test cases: {total}")
                    
                    for i, result in enumerate(test_case_results[:3], 1):
                        scenario_id = result.get("scenario_id", "?")
                        tc_count = len(result.get("test_cases", []))
                        print(f"      {i}. {scenario_id}: {tc_count} test cases")
                    
                    if len(test_case_results) > 3:
                        print(f"      ... and {len(test_case_results) - 3} more")
                
                # Check format 2: output.data.test_case_results
                data = output.get("data", {})
                test_case_results_nested = data.get("test_case_results", [])
                if test_case_results_nested:
                    print(f"   ✅ Found test_case_results at output.data.test_case_results")
                    total = sum(len(r.get("test_cases", [])) for r in test_case_results_nested)
                    print(f"   📊 Total test cases: {total}")
                
                # Check format 3: output.test_cases
                test_cases = output.get("test_cases", [])
                if test_cases:
                    print(f"   ✅ Found test_cases at output.test_cases")
                    print(f"   📊 Count: {len(test_cases)}")
                
                # Check metadata
                metadata = output.get("metadata", {})
                if metadata:
                    print(f"\n   📝 Metadata:")
                    total_from_metadata = metadata.get("total_test_cases", 0)
                    if total_from_metadata:
                        print(f"      - total_test_cases: {total_from_metadata}")
            
            print()

async def main():
    await test_manual_analysis()

if __name__ == "__main__":
    asyncio.run(main())
