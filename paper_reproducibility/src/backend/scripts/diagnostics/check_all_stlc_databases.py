"""
Check all STLC databases for session_history
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_all_stlc_dbs():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    
    db_names = ["stlc_database", "stlc_db", "modular_test_scenario_gen"]
    
    for db_name in db_names:
        print(f"\n{'=' * 70}")
        print(f"DATABASE: {db_name}")
        print(f"{'=' * 70}")
        
        db = client[db_name]
        collections = await db.list_collection_names()
        
        print(f"Collections: {collections}")
        
        for coll_name in collections:
            coll = db[coll_name]
            count = await coll.count_documents({})
            print(f"\n  {coll_name}: {count} documents")
            
            if count > 0:
                sample = await coll.find_one({})
                print(f"    Sample keys: {list(sample.keys())[:10]}")  # First 10 keys
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_all_stlc_dbs())
