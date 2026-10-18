from core.database import get_db
import json

db = get_db()
collection = db["session_history"]

print("=== Investigating Document Structure ===")

# Get a sample document
sample = collection.find_one({"processes.test_case_generation": {"$exists": True}})
if sample:
    print("Sample document keys:", list(sample.keys()))
    
    # Check if processes is a dict or list
    processes = sample.get("processes", {})
    print(f"Processes type: {type(processes)}")
    
    if isinstance(processes, dict):
        print("Processes keys:", list(processes.keys()))
        for key, value in processes.items():
            print(f"  {key}: {type(value)}")
            if isinstance(value, dict) and "test_case_generation" in value:
                tcg = value["test_case_generation"]
                print(f"    test_case_generation type: {type(tcg)}")
                if isinstance(tcg, dict):
                    print(f"    test_case_generation keys: {list(tcg.keys())}")
    elif isinstance(processes, list):
        print(f"Processes is a list with {len(processes)} items")
        for i, item in enumerate(processes):
            print(f"  Item {i}: {type(item)} - {str(item)[:100]}...")
    
    # Try to find test_case_generation differently
    if "test_case_generation" in sample:
        print("Found test_case_generation at root level")
        tcg = sample["test_case_generation"]
        print(f"Type: {type(tcg)}")
        
else:
    print("No sample document found")
