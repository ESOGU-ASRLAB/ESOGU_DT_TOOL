from core.database import get_db
import json

db = get_db()
collection = db["session_history"]

# Look for the specific session_id from the user's request
target_session_id = "a73c8ab2-cd5d-45be-84c5-b32d71fde91e"

print(f"=== Full Document Analysis for {target_session_id} ===")

doc = collection.find_one({"session_id": target_session_id})
if doc:
    print("Document structure:")
    
    # Print the full structure to understand the data
    processes = doc.get("processes", {})
    
    if "test_case_generation" in processes:
        tcg = processes["test_case_generation"]
        print("test_case_generation structure:")
        print(f"  Keys: {list(tcg.keys())}")
        
        if "output" in tcg:
            output = tcg["output"]
            print(f"  output keys: {list(output.keys())}")
            
            if "data" in output:
                data = output["data"]
                print(f"  data keys: {list(data.keys())}")
                print(f"  data content: {json.dumps(data, indent=2, default=str)[:500]}...")
else:
    print("Document not found!")

# Let's also check if the structure you provided might be in a test_scenarios collection
print("\n=== Checking test_scenarios collection ===")
test_scenarios_collection = db["test_scenarios"]
test_scenarios_count = test_scenarios_collection.count_documents({})
print(f"test_scenarios collection has {test_scenarios_count} documents")

if test_scenarios_count > 0:
    # Check for the specific session_id
    test_doc = test_scenarios_collection.find_one({"session_id": target_session_id})
    if test_doc:
        print(f"Found document in test_scenarios collection!")
        processes = test_doc.get("processes", {})
        if "test_case_generation" in processes:
            tcg = processes["test_case_generation"]
            output = tcg.get("output", {})
            data = output.get("data", {})
            test_case_results = data.get("test_case_results", [])
            print(f"test_scenarios -> test_case_results: {len(test_case_results)}")
    else:
        print("Session not found in test_scenarios collection")
