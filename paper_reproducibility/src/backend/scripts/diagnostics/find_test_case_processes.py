"""
Check for test_case_generation and test_case_optimization in sessions
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_test_case_processes():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["stlc_database"]
    collection = db["session_history"]
    
    sessions = await collection.find({}).to_list(length=None)
    
    print(f"Total sessions: {len(sessions)}\n")
    
    # Count different processes
    processes_count = {}
    
    for session in sessions:
        processes = session.get("processes", {})
        for proc_name in processes.keys():
            processes_count[proc_name] = processes_count.get(proc_name, 0) + 1
    
    print("=" * 70)
    print("PROCESS FREQUENCY")
    print("=" * 70)
    for proc_name, count in sorted(processes_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {proc_name}: {count}")
    
    # Check test_case_generation and test_case_optimization
    print(f"\n{'=' * 70}")
    print("SESSIONS WITH TEST CASE PROCESSES")
    print(f"{'=' * 70}")
    
    for idx, session in enumerate(sessions, 1):
        session_id = session.get("session_id", "Unknown")
        processes = session.get("processes", {})
        
        has_tc_gen = "test_case_generation" in processes
        has_tc_opt = "test_case_optimization" in processes
        
        if has_tc_gen or has_tc_opt:
            print(f"\nSession {idx}: {session_id[:40]}...")
            if has_tc_gen:
                tc_gen = processes["test_case_generation"]
                print(f"  ✅ test_case_generation")
                if "output" in tc_gen:
                    output = tc_gen["output"]
                    print(f"     output keys: {list(output.keys()) if isinstance(output, dict) else type(output)}")
            
            if has_tc_opt:
                tc_opt = processes["test_case_optimization"]
                print(f"  ✅ test_case_optimization")
                if "output" in tc_opt:
                    output = tc_opt["output"]
                    print(f"     output keys: {list(output.keys()) if isinstance(output, dict) else type(output)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_test_case_processes())
