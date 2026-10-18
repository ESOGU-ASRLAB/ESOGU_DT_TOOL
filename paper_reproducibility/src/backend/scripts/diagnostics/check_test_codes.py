"""
Check for test codes in processes collection
"""
import asyncio
from core.database import get_database

async def check_test_codes():
    db = await get_database()
    
    # Check the processes collection
    print("=" * 80)
    print("CHECKING PROCESSES COLLECTION")
    print("=" * 80)
    
    # Find documents with test_code_generation
    query = {"process_title": {"$regex": "test.*code", "$options": "i"}}
    processes = await db.processes.find(query).to_list(length=10)
    
    print(f"\nFound {len(processes)} processes matching 'test code'")
    
    for proc in processes:
        print(f"\n" + "=" * 80)
        print(f"Process: {proc.get('process_title')}")
        print(f"Process Name: {proc.get('process_name')}")
        print(f"Session ID: {proc.get('session_id')}")
        print(f"Status: {proc.get('status')}")
        
        # Check for tests
        if "tests" in proc:
            tests = proc["tests"]
            print(f"\n✅ Found 'tests' field with {len(tests) if isinstance(tests, list) else 'N/A'} items")
            if isinstance(tests, list) and tests:
                print("\nFirst test keys:")
                for key in tests[0].keys():
                    print(f"  - {key}")
                
                # Show test_id and test_code presence
                print("\nTest IDs and code presence:")
                for test in tests[:5]:  # First 5
                    test_id = test.get("test_id") or test.get("test_case_id")
                    has_code = "test_code" in test and test["test_code"]
                    code_len = len(test.get("test_code", "")) if has_code else 0
                    print(f"  - {test_id}: {'✅ has code' if has_code else '❌ no code'} ({code_len} chars)")
        
        # Check for generated_tests
        if "generated_tests" in proc:
            generated_tests = proc["generated_tests"]
            print(f"\n✅ Found 'generated_tests' field")
        
        # Show all top-level keys
        print(f"\nAll keys: {list(proc.keys())}")

if __name__ == "__main__":
    asyncio.run(check_test_codes())
