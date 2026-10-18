"""
Test MongoDB connection and list collections
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_mongo():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    
    # List all databases
    print("=" * 70)
    print("DATABASES")
    print("=" * 70)
    db_list = await client.list_database_names()
    for db_name in db_list:
        print(f"  {db_name}")
    
    # Check stlc_database database
    print(f"\n{'=' * 70}")
    print("STLC_DATABASE COLLECTIONS")
    print(f"{'=' * 70}")
    
    db = client["stlc_database"]
    collections = await db.list_collection_names()
    for coll_name in collections:
        coll = db[coll_name]
        count = await coll.count_documents({})
        print(f"  {coll_name}: {count} documents")
        
        # Sample one document
        if count > 0:
            sample = await coll.find_one({})
            print(f"    Sample keys: {list(sample.keys())}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_mongo())
