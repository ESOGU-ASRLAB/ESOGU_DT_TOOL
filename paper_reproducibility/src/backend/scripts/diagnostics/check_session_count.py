"""
Check the number of records in session_history collection
"""
import asyncio
from core.database import get_database

async def check_session_count():
    """Check total count of session_history records"""
    db = await get_database()
    collection = db["session_history"]
    
    # Get total count
    total_count = await collection.count_documents({})
    
    print("=" * 80)
    print("SESSION HISTORY COLLECTION COUNT")
    print("=" * 80)
    print(f"\nTotal Records: {total_count}")
    print("=" * 80)
    
    # Get some statistics
    print("\nAdditional Statistics:")
    print("-" * 80)
    
    # Count by process type
    pipeline = [
        {
            "$project": {
                "processes": {"$objectToArray": "$processes"}
            }
        },
        {
            "$unwind": "$processes"
        },
        {
            "$group": {
                "_id": "$processes.k",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        }
    ]
    
    process_counts = await collection.aggregate(pipeline).to_list(None)
    
    print("\nRecords by Process Type:")
    for item in process_counts:
        print(f"  - {item['_id']}: {item['count']} records")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(check_session_count())
