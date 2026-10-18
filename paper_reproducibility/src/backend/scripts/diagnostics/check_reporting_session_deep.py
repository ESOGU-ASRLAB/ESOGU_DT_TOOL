"""
Deep Check Test Reporting Session Structure
"""

import asyncio
import json
from core.database import get_database

async def check_reporting_session_structure():
    """Check structure of test reporting sessions"""
    db = await get_database()
    collection = db["session_history"]
    
    # Find a test reporting session
    session = await collection.find_one({"session_id": "test_report_20260113_175728"})
    
    if not session:
        print("❌ Session not found")
        # Try to find any test_report session
        cursor = collection.find({"session_id": {"$regex": "test_report"}}).limit(1)
        sessions = await cursor.to_list(length=1)
        if sessions:
            session = sessions[0]
            print(f"✅ Found alternative session: {session.get('session_id')}")
        else:
            print("❌ No test_report sessions found")
            return
    
    session_id = session.get("session_id", "unknown")
    
    print(f"\n{'='*80}")
    print(f"📊 SESSION STRUCTURE: {session_id}")
    print(f"{'='*80}\n")
    
    print("Top-level keys:")
    for key in session.keys():
        print(f"   - {key}")
    
    # Check if there's a 'data' field
    if "data" in session:
        print(f"\n📦 data keys: {list(session['data'].keys())}")
        data = session.get("data", {})
        
        # Check for test scenarios
        if "test_scenarios" in data:
            scenarios = data.get("test_scenarios", {})
            if isinstance(scenarios, dict):
                test_scenarios = scenarios.get("TestScenarios", [])
                print(f"   ✅ Test Scenarios: {len(test_scenarios)}")
        
        # Check for test cases
        if "test_cases" in data:
            test_cases = data.get("test_cases", [])
            print(f"   ✅ Test Cases (flat): {len(test_cases)}")
        
        if "test_case_results" in data:
            test_case_results = data.get("test_case_results", [])
            print(f"   ✅ Test Case Results: {len(test_case_results)} groups")
            total = sum(len(r.get("test_cases", [])) for r in test_case_results)
            print(f"      Total test cases: {total}")
    
    # Check processes
    if "processes" in session:
        processes = session.get("processes", {})
        print(f"\n📦 processes keys: {list(processes.keys())}")
    
    # Show full structure (limited)
    print(f"\n{'='*80}")
    print("RAW STRUCTURE (first 3000 chars):")
    print(f"{'='*80}")
    session_json = json.dumps(session, indent=2, default=str)
    print(session_json[:3000])
    if len(session_json) > 3000:
        print(f"\n... ({len(session_json) - 3000} more characters)")

async def main():
    await check_reporting_session_structure()

if __name__ == "__main__":
    asyncio.run(main())
