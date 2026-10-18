"""
Check what processes exist in sessions
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from collections import Counter

async def check_processes():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["stlc_database"]
    collection = db["session_history"]
    
    # Get all sessions
    sessions = await collection.find({}).to_list(length=None)
    
    print(f"Total sessions: {len(sessions)}\n")
    
    all_processes = []
    
    for session in sessions:
        session_name = session.get("session_name", "Unknown")
        process_data = session.get("process_data", {})
        
        print(f"\n{'=' * 70}")
        print(f"Session: {session_name}")
        print(f"{'=' * 70}")
        print(f"Processes found: {list(process_data.keys())}")
        
        all_processes.extend(process_data.keys())
    
    print(f"\n{'=' * 70}")
    print("PROCESS FREQUENCY")
    print(f"{'=' * 70}")
    
    counts = Counter(all_processes)
    for process, count in counts.most_common():
        print(f"  {process}: {count}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_processes())
