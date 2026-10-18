"""
Test robot_docker_executor's _fetch_test_cases method
"""
import asyncio
from core.database import get_database
from services.robot_docker_executor import RobotDockerExecutor

async def test_fetch():
    executor = RobotDockerExecutor()
    db = await get_database()
    
    # Test with actual process name and test IDs
    process_name = "ROS Test-27 Temmuz 2026"
    test_ids = ["TC_001", "TC_002", "TC_003", "TC_004"]
    
    print("=" * 80)
    print(f"Testing _fetch_test_cases")
    print(f"Process: {process_name}")
    print(f"Test IDs: {test_ids}")
    print("=" * 80)
    
    test_codes = await executor._fetch_test_cases(db, process_name, test_ids)
    
    print(f"\n✅ Fetched {len(test_codes)} test codes")
    
    for test in test_codes:
        test_id = test.get('test_id')
        test_name = test.get('test_case_name')
        code_len = len(test.get('test_code', ''))
        has_code = code_len > 0
        
        print(f"\n  Test ID: {test_id}")
        print(f"    Name: {test_name}")
        print(f"    Has Code: {has_code} ({code_len} chars)")
        if has_code:
            code_preview = test.get('test_code', '')[:150]
            print(f"    Code Preview: {code_preview}...")

if __name__ == "__main__":
    asyncio.run(test_fetch())
