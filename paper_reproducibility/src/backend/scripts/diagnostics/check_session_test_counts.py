"""
Check Test Counts for Specific Session
Verifies test scenario and test case counts for closure report
"""

import asyncio
import json
from core.database import get_database

async def check_session_counts(session_id: str):
    """
    Check test scenario and test case counts for a specific session
    
    Args:
        session_id: The session ID to check
    """
    db = await get_database()
    collection = db["session_history"]
    
    # Find the session
    session = await collection.find_one({"session_id": session_id})
    
    if not session:
        print(f"❌ Session not found: {session_id}")
        return
    
    print(f"\n{'='*80}")
    print(f"📊 SESSION ANALYSIS: {session_id}")
    print(f"{'='*80}\n")
    
    # Check creation date
    created_at = session.get("created_at")
    print(f"🕒 Created At: {created_at}")
    print(f"   Type: {type(created_at)}")
    
    processes = session.get("processes", {})
    print(f"\n📦 Processes found: {list(processes.keys())}")
    
    # Counter variables
    total_scenarios = 0
    total_test_cases_generated = 0
    total_test_cases_optimized = 0
    
    # Check Test Scenario Generation
    print(f"\n{'='*80}")
    print("1️⃣  TEST SCENARIO GENERATION")
    print(f"{'='*80}")
    
    if "test_scenario_generation" in processes:
        tsg = processes["test_scenario_generation"]
        output = tsg.get("output", {})
        model = tsg.get("used_model", "N/A")
        
        print(f"   Model Used: {model}")
        
        test_scenarios = output.get("test_scenarios", {})
        scenarios = test_scenarios.get("TestScenarios", [])
        total_scenarios = len(scenarios)
        
        print(f"   ✅ Test Scenarios Found: {total_scenarios}")
        
        # Show first few scenarios
        for i, scenario in enumerate(scenarios[:3], 1):
            scenario_id = scenario.get("ScenarioID", "N/A")
            title = scenario.get("Title", "N/A")
            category = scenario.get("Category", "N/A")
            print(f"      {i}. {scenario_id} - {title} ({category})")
        
        if len(scenarios) > 3:
            print(f"      ... and {len(scenarios) - 3} more scenarios")
        
        # Metadata
        metadata = output.get("metadata", {})
        test_type = metadata.get("test_type", "Unknown")
        test_category = metadata.get("test_category", "Unknown")
        print(f"\n   📝 Metadata:")
        print(f"      - Test Type: {test_type}")
        print(f"      - Test Category: {test_category}")
    else:
        print("   ❌ No test_scenario_generation process found")
    
    # Check Test Case Generation
    print(f"\n{'='*80}")
    print("2️⃣  TEST CASE GENERATION")
    print(f"{'='*80}")
    
    if "test_case_generation" in processes:
        tcg = processes["test_case_generation"]
        output = tcg.get("output", {})
        model = tcg.get("used_model", "N/A")
        
        print(f"   Model Used: {model}")
        
        # Support multiple data structures
        # Structure 1: output['test_case_results'] (direct)
        test_case_results = output.get("test_case_results", [])
        
        # Structure 2: output['data']['test_case_results'] (nested in data)
        if not test_case_results:
            data = output.get("data", {})
            test_case_results = data.get("test_case_results", [])
        
        print(f"   📦 Test Case Result Groups: {len(test_case_results)}")
        
        for i, result in enumerate(test_case_results, 1):
            scenario_id = result.get("scenario_id", "unknown")
            test_cases = result.get("test_cases", [])
            num_cases = len(test_cases)
            total_test_cases_generated += num_cases
            
            print(f"      {i}. Scenario {scenario_id}: {num_cases} test cases")
            
            # Show first test case as sample
            if test_cases:
                first_tc = test_cases[0]
                tc_id = first_tc.get("TestCaseID", "N/A")
                tc_title = first_tc.get("Title", "N/A")
                print(f"         Sample: {tc_id} - {tc_title}")
        
        print(f"\n   ✅ Total Test Cases Generated: {total_test_cases_generated}")
    else:
        print("   ❌ No test_case_generation process found")
    
    # Check Test Case Optimization
    print(f"\n{'='*80}")
    print("3️⃣  TEST CASE OPTIMIZATION")
    print(f"{'='*80}")
    
    if "test_case_optimization" in processes:
        tco = processes["test_case_optimization"]
        output = tco.get("output", {})
        model = tco.get("used_model", "N/A")
        
        print(f"   Model Used: {model}")
        
        optimized_test_cases = output.get("optimized_test_cases", [])
        total_test_cases_optimized = len(optimized_test_cases)
        
        print(f"   ✅ Optimized Test Cases: {total_test_cases_optimized}")
        
        # Show first few optimized test cases
        for i, tc in enumerate(optimized_test_cases[:3], 1):
            tc_id = tc.get("TestCaseID", "N/A")
            tc_title = tc.get("Title", "N/A")
            print(f"      {i}. {tc_id} - {tc_title}")
        
        if len(optimized_test_cases) > 3:
            print(f"      ... and {len(optimized_test_cases) - 3} more optimized test cases")
    else:
        print("   ❌ No test_case_optimization process found")
    
    # Check Test Execution
    print(f"\n{'='*80}")
    print("4️⃣  TEST EXECUTION")
    print(f"{'='*80}")
    
    if "test_execution" in processes:
        te = processes["test_execution"]
        output = te.get("output", {})
        
        terminal_output = output.get("terminal_output", "")
        
        # Parse execution results
        import re
        passed_match = re.search(r'(\d+)\s+passed', terminal_output)
        failed_match = re.search(r'(\d+)\s+failed', terminal_output)
        skipped_match = re.search(r'(\d+)\s+skipped', terminal_output)
        
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0
        total = passed + failed + skipped
        
        print(f"   ✅ Tests Executed: {total}")
        print(f"      - Passed: {passed}")
        print(f"      - Failed: {failed}")
        print(f"      - Skipped: {skipped}")
        
        if total > 0:
            pass_rate = (passed / total) * 100
            print(f"      - Pass Rate: {pass_rate:.2f}%")
    else:
        print("   ❌ No test_execution process found")
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY FOR CLOSURE REPORT")
    print(f"{'='*80}")
    print(f"   Test Scenarios: {total_scenarios}")
    print(f"   Test Cases Generated: {total_test_cases_generated}")
    print(f"   Test Cases Optimized: {total_test_cases_optimized}")
    
    if total_test_cases_generated > 0:
        optimization_rate = (total_test_cases_optimized / total_test_cases_generated) * 100
        print(f"   Optimization Rate: {optimization_rate:.2f}%")
    
    print(f"\n{'='*80}\n")

async def main():
    """Main function"""
    session_id = "project.xml Test Scenario&Test Cases"
    
    print("\n🔍 Checking test counts for specific session...")
    print(f"Session ID: {session_id}")
    
    await check_session_counts(session_id)

if __name__ == "__main__":
    asyncio.run(main())
