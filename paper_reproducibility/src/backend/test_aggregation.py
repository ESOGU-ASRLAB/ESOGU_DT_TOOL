import asyncio
from core.database import get_database
import json

async def test_aggregation():
    try:
        db = await get_database()
        collection = db["session_history"]
        
        # Test aggregation pipeline exactly as in the endpoint
        pipeline = [
            {
                "$match": {
                    "processes.test_scenario_generation": {"$exists": True},
                    "processes.test_scenario_generation.process_title": {
                        "$exists": True, 
                        "$ne": "", 
                        "$ne": None
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "session_id": 1,
                    "created_at": {"$dateToString": {"format": "%Y-%m-%d %H:%M:%S", "date": "$created_at"}},
                    "process_title": "$processes.test_scenario_generation.process_title",
                    "test_type": "$processes.test_scenario_generation.output.metadata.test_type",
                    "test_category": "$processes.test_scenario_generation.output.metadata.test_category"
                }
            },
            {
                "$sort": {"created_at": -1}
            }
        ]
        
        print("=== TESTING AGGREGATION PIPELINE ===")
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        print(f"Found {len(results)} results:")
        for result in results:
            print(json.dumps(result, indent=2, default=str))
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_aggregation())
