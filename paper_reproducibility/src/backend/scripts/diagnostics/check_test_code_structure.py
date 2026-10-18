"""
Check test code generation structure in database
"""
import asyncio
from core.database import get_database

async def check_structure():
    db = await get_database()
    
    # Find a session with test code generation
    query = {
        "processes.test_code_generation": {"$exists": True}
    }
    
    session = await db.session_history.find_one(query)
    
    if session:
        print("=" * 80)
        print("FOUND SESSION WITH TEST CODE GENERATION")
        print("=" * 80)
        
        processes = session.get("processes", {})
        test_code_gen = processes.get("test_code_generation", {})
        
        print(f"\nProcess Name: {test_code_gen.get('process_name')}")
        print(f"\nTop-level keys in test_code_generation:")
        for key in test_code_gen.keys():
            print(f"  - {key}")
        
        # Check for tests
        if "tests" in test_code_gen:
            tests = test_code_gen["tests"]
            print(f"\n✅ Found 'tests' field with {len(tests)} items")
            if tests:
                print("\nFirst test structure:")
                first_test = tests[0]
                for key, value in first_test.items():
                    if key == "test_code":
                        print(f"  - {key}: <code present, length={len(value) if value else 0}>")
                    else:
                        print(f"  - {key}: {value if not isinstance(value, str) or len(value) < 100 else value[:100] + '...'}")
        
        # Check for generated_tests
        if "generated_tests" in test_code_gen:
            generated_tests = test_code_gen["generated_tests"]
            print(f"\n✅ Found 'generated_tests' field with {len(generated_tests)} items")
            if generated_tests:
                print("\nFirst generated test structure:")
                first_test = generated_tests[0]
                for key, value in first_test.items():
                    if key == "test_code":
                        print(f"  - {key}: <code present, length={len(value) if value else 0}>")
                    else:
                        print(f"  - {key}: {value if not isinstance(value, str) or len(value) < 100 else value[:100] + '...'}")
        
        # Check other possible fields
        other_fields = [k for k in test_code_gen.keys() if k not in ["process_name", "tests", "generated_tests"]]
        if other_fields:
            print(f"\nOther fields: {other_fields}")
    
    else:
        print("❌ No session found with test_code_generation")

if __name__ == "__main__":
    asyncio.run(check_structure())
