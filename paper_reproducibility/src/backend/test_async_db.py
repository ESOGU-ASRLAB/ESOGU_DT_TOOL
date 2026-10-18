import asyncio
from core.database import get_database

async def test_async_db():
    try:
        db = await get_database()
        collection = db["session_history"]
        count = await collection.count_documents({})
        print(f"Async MongoDB connection successful. Total sessions: {count}")
        return True
    except Exception as e:
        print(f"Async MongoDB connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_async_db())
    print(f"Test result: {result}")
