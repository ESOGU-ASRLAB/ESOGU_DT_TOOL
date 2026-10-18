"""
Check actual field names in test cases
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

async def check_test_case_fields():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["stlc_database"]
    collection = db["session_history"]
    
    session = await collection.find_one({"session_id": "16f91ead-b607-43e2-96a2-a74d0d4a3543"})
    
    tc_gen = session["processes"]["test_case_generation"]
    output = tc_gen["output"]
    
    first_result = output["test_case_results"][0]
    first_tc = first_result["test_cases"][0]
    
    print("=" * 70)
    print("FIRST TEST CASE FULL STRUCTURE")
    print("=" * 70)
    print(json.dumps(first_tc, indent=2, ensure_ascii=False))
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_test_case_fields())
