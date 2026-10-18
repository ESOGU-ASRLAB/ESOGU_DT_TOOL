"""
Test optimization quality calculation
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json
from services.quality_metrics_calculator import quality_calculator

async def test_optimization_quality():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["stlc_database"]
    collection = db["session_history"]
    
    # Use optimization session: 167cf610-926f-458c-9000-089661329cdd
    session = await collection.find_one({"session_id": "167cf610-926f-458c-9000-089661329cdd"})
    
    tc_opt = session["processes"]["test_case_optimization"]
    output = tc_opt["output"]
    
    print("=" * 70)
    print("TEST CASE OPTIMIZATION OUTPUT")
    print("=" * 70)
    print(f"Output keys: {list(output.keys())}")
    
    unique = output.get("unique_test_cases", [])
    similar = output.get("similar_test_cases", [])
    
    print(f"\nUnique test cases: {len(unique)}")
    print(f"Similar test cases: {len(similar)}")
    print(f"Total (original): {output.get('total_test_cases', 'N/A')}")
    print(f"Total comparisons: {output.get('total_comparisons', 'N/A')}")
    
    if len(unique) > 0:
        print(f"\nFirst unique test case keys: {list(unique[0].keys())}")
        print(f"\nSample: {json.dumps(unique[0], indent=2, default=str)[:500]}")
    
    # Test quality calculation
    print(f"\n{'=' * 70}")
    print("QUALITY CALCULATION")
    print(f"{'=' * 70}")
    
    quality = quality_calculator.calculate_process_quality("test_case_optimization", output)
    
    print(json.dumps(quality, indent=2))
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_optimization_quality())
