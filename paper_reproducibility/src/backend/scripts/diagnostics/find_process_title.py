from core.database import get_db
import json

db = get_db()
collection = db["session_history"]

target_session_id = "a73c8ab2-cd5d-45be-84c5-b32d71fde91e"

print(f"=== Finding where '26_son' is stored ===")

doc = collection.find_one({"session_id": target_session_id})
if doc:
    processes = doc.get("processes", {})
    
    # Check test_case_generation
    if "test_case_generation" in processes:
        tcg = processes["test_case_generation"]
        print("test_case_generation structure:")
        print(f"  selected_process_title: {tcg.get('selected_process_title')}")
        
        output = tcg.get("output", {})
        metadata = output.get("metadata", {})
        print(f"  output.metadata: {metadata}")
    
    # Check test_scenario_generation
    if "test_scenario_generation" in processes:
        tsg = processes["test_scenario_generation"]
        print("test_scenario_generation structure:")
        print(f"  Keys: {list(tsg.keys())}")
        print(f"  process_title: {tsg.get('process_title')}")
        
        if "output" in tsg:
            output = tsg["output"]
            metadata = output.get("metadata", {})
            print(f"  output.metadata: {metadata}")

print("\nBased on this, the service should be using the correct path:")
