"""
Check session_history structure in stlc_database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

async def check_session_history():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["stlc_database"]
    collection = db["session_history"]
    
    # Get one session
    session = await collection.find_one({})
    
    print("=" * 70)
    print("SESSION HISTORY STRUCTURE")
    print("=" * 70)
    print(f"\nTop-level keys: {list(session.keys())}")
    
    # Check processes
    if "processes" in session:
        processes = session["processes"]
        print(f"\nprocesses type: {type(processes)}")
        if isinstance(processes, list):
            print(f"processes length: {len(processes)}")
            if len(processes) > 0:
                print(f"\nFirst process keys: {list(processes[0].keys())}")
                print(f"First process: {json.dumps(processes[0], indent=2, default=str)[:500]}")
        elif isinstance(processes, dict):
            print(f"processes keys: {list(processes.keys())}")
    
    # Save full sample
    with open("session_history_sample.json", "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"\n💾 Full session saved to: session_history_sample.json")
    
    # Check all sessions for test_scenario_generation
    all_sessions = await collection.find({}).to_list(length=None)
    print(f"\n{'=' * 70}")
    print(f"CHECKING ALL {len(all_sessions)} SESSIONS")
    print(f"{'=' * 70}")
    
    for idx, sess in enumerate(all_sessions, 1):
        processes = sess.get("processes", [])
        if isinstance(processes, list):
            process_names = [p.get("process_name") or p.get("process_type") for p in processes]
            print(f"\nSession {idx}: {sess.get('session_id', 'Unknown')[:20]}...")
            print(f"  Processes: {process_names}")
            
            # Check for test_scenario_generation
            for proc in processes:
                if proc.get("process_name") == "test_scenario_generation" or proc.get("process_type") == "test_scenario_generation":
                    print(f"  ✅ Has test_scenario_generation")
                    print(f"     Keys: {list(proc.keys())}")
                    if "output" in proc:
                        output = proc["output"]
                        print(f"     output keys: {list(output.keys()) if isinstance(output, dict) else type(output)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_session_history())
