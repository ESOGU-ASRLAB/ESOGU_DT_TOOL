"""
Test unique_id implementation end-to-end
"""
import asyncio
from core.database import get_database
from services.robot_docker_executor import RobotDockerExecutor

async def test():
    db = await get_database()
    executor = RobotDockerExecutor()
    
    process_name = "ROS Test-27 Temmuz 2026"
    
    print("=" * 80)
    print("STEP 1: Fetch all test codes (like frontend does)")
    print("=" * 80)
    
    # Simulate what test_code_generation_service does
    pipeline = [
        {
            "$match": {
                "processes.test_code_generation": {"$exists": True},
                "processes.test_code_generation.process_name": process_name
            }
        },
        {
            "$project": {
                "session_id": 1,
                "timestamp": "$processes.test_code_generation.timestamp",
                "generated_tests": "$processes.test_code_generation.output.generated_tests",
                "process_name": "$processes.test_code_generation.process_name"
            }
        },
        {
            "$sort": {"timestamp": -1}
        },
        {
            "$limit": 1
        }
    ]
    
    results = await db.session_history.aggregate(pipeline).to_list(length=None)
    latest_session = results[0]
    generated_tests = latest_session.get("generated_tests", [])
    
    # Format like service does
    formatted_tests = []
    for test in generated_tests:
        if test.get('status') == 'success':
            formatted_tests.append({
                "unique_id": test.get("unique_id", ""),
                "test_id": test.get("test_case_id", ""),
                "test_case_name": test.get("title", ""),
                "status": test.get("status", "unknown")
            })
    
    print(f"✅ Found {len(formatted_tests)} successful test codes")
    
    # Show first 4
    print("\nFirst 4 test codes (would be shown in frontend):")
    for i, test in enumerate(formatted_tests[:4], 1):
        print(f"  {i}. {test['test_id']}: {test['test_case_name'][:60]}...")
        print(f"     unique_id: {test['unique_id']}")
    
    print("\n" + "=" * 80)
    print("STEP 2: User selects 4 tests (simulate frontend selection)")
    print("=" * 80)
    
    # Select first 4 unique_ids
    selected_unique_ids = [test['unique_id'] for test in formatted_tests[:4]]
    print(f"Selected unique_ids: {selected_unique_ids}")
    
    print("\n" + "=" * 80)
    print("STEP 3: Backend fetches test codes for execution")
    print("=" * 80)
    
    test_codes = await executor._fetch_test_cases(db, process_name, selected_unique_ids)
    
    print(f"\n✅ Fetched {len(test_codes)} test codes for execution")
    
    if len(test_codes) == len(selected_unique_ids):
        print("✅ SUCCESS: Exact match - no duplicates!")
    else:
        print(f"❌ PROBLEM: Expected {len(selected_unique_ids)} but got {len(test_codes)}")
    
    print("\nFetched test codes:")
    for i, test in enumerate(test_codes, 1):
        print(f"  {i}. {test['test_id']}: {test['test_case_name'][:60]}...")
        print(f"     unique_id: {test['unique_id']}")
        print(f"     code_length: {len(test['test_code'])} chars")

if __name__ == "__main__":
    asyncio.run(test())
