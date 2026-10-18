import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI
import json

async def check_test_structure():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client['stlc_database']
    
    # Find the ROS Test session
    result = await db.session_history.find_one(
        {'processes.test_code_generation.process_name': 'ROS Test-27 Temmuz 2026'},
        {'processes.test_code_generation.output.generated_tests': 1}
    )
    
    if result:
        try:
            generated_tests = result['processes']['test_code_generation']['output']['generated_tests']
            if generated_tests and len(generated_tests) > 0:
                print("First test structure:")
                print(json.dumps(generated_tests[0], indent=2, default=str))
                print("\nAll field names in first test:")
                print(list(generated_tests[0].keys()))
            else:
                print("generated_tests is empty or None")
        except KeyError as e:
            print(f"KeyError: {e}")
            print("Available keys:", result.keys())
    else:
        print("No session found")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_test_structure())
