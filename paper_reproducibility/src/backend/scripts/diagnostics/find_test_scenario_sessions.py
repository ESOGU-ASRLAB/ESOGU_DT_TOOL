"""
Check all sessions in stlc_database for test_scenario_generation
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_sessions_with_test_scenarios():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["stlc_database"]
    collection = db["session_history"]
    
    sessions = await collection.find({}).to_list(length=None)
    
    print(f"Total sessions: {len(sessions)}\n")
    
    count_with_test_scenarios = 0
    
    for idx, session in enumerate(sessions, 1):
        session_id = session.get("session_id", "Unknown")
        processes = session.get("processes", {})
        
        # Check if test_scenario_generation exists in processes
        if "test_scenario_generation" in processes:
            count_with_test_scenarios += 1
            print(f"\n{'=' * 70}")
            print(f"Session {idx}: {session_id[:40]}...")
            print(f"{'=' * 70}")
            
            tsg = processes["test_scenario_generation"]
            print(f"  Keys: {list(tsg.keys())}")
            
            if "output" in tsg:
                output = tsg["output"]
                print(f"  output keys: {list(output.keys()) if isinstance(output, dict) else type(output)}")
                
                if isinstance(output, dict) and "test_scenarios" in output:
                    test_scenarios = output["test_scenarios"]
                    if isinstance(test_scenarios, dict) and "TestScenarios" in test_scenarios:
                        scenario_list = test_scenarios["TestScenarios"]
                        print(f"  TestScenarios count: {len(scenario_list)}")
                        if len(scenario_list) > 0:
                            print(f"  First scenario keys: {list(scenario_list[0].keys())}")
    
    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total sessions: {len(sessions)}")
    print(f"Sessions with test_scenario_generation: {count_with_test_scenarios}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_sessions_with_test_scenarios())
