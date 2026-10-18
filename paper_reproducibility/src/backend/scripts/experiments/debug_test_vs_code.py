"""
Debug: Test Cases vs Test Codes
Check what's in the database for test_code_generation
"""
import asyncio
from core.database import get_database

async def debug():
    db = await get_database()
    
    print("=" * 80)
    print("CHECKING TEST CODE GENERATION DATA")
    print("=" * 80)
    
    # Get a sample from test_code_generation
    pipeline = [
        {
            "$match": {
                "processes.test_code_generation": {"$exists": True}
            }
        },
        {
            "$project": {
                "session_id": 1,
                "process_name": "$processes.test_code_generation.process_name",
                "timestamp": "$processes.test_code_generation.timestamp",
                "generated_tests": "$processes.test_code_generation.output.generated_tests"
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
    
    if results:
        session = results[0]
        print(f"\n✅ Found test_code_generation session")
        print(f"   Session ID: {session.get('session_id')}")
        print(f"   Process Name: {session.get('process_name')}")
        
        generated_tests = session.get('generated_tests', [])
        print(f"\n📊 Generated Tests: {len(generated_tests)} items")
        
        if generated_tests:
            print("\n" + "=" * 80)
            print("FIRST TEST STRUCTURE:")
            print("=" * 80)
            first_test = generated_tests[0]
            
            for key, value in first_test.items():
                if key == "code":
                    code_len = len(value) if value else 0
                    has_code = code_len > 0
                    print(f"  ✅ {key}: {'HAS CODE' if has_code else 'NO CODE'} ({code_len} chars)")
                    if has_code:
                        print(f"      Preview: {value[:100]}...")
                else:
                    print(f"  - {key}: {value if not isinstance(value, str) or len(value) < 100 else value[:100] + '...'}")
            
            print("\n" + "=" * 80)
            print("ALL TESTS IDs AND CODE STATUS:")
            print("=" * 80)
            for idx, test in enumerate(generated_tests[:10], 1):  # First 10
                test_id = test.get('test_case_id', 'NO_ID')
                has_code = bool(test.get('code'))
                code_len = len(test.get('code', ''))
                status = test.get('status', 'unknown')
                print(f"  {idx}. {test_id}: status={status}, has_code={has_code}, code_len={code_len}")
    else:
        print("\n❌ No test_code_generation session found")
    
    print("\n" + "=" * 80)
    print("CHECKING PROCESS NAMES")
    print("=" * 80)
    
    # Get unique process names
    process_names = await db.session_history.distinct(
        "processes.test_code_generation.process_name",
        {"processes.test_code_generation": {"$exists": True}}
    )
    
    print(f"Process names with test code generation: {len(process_names)}")
    for name in process_names[:5]:
        print(f"  - {name}")

if __name__ == "__main__":
    asyncio.run(debug())
