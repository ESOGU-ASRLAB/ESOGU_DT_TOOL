from core.database import get_db

db = get_db()
collection = db["session_history"]

print("=== Session History Collection Analysis ===")
total_docs = collection.count_documents({})
print(f"Total documents: {total_docs}")

# Check for documents with test_case_generation
test_case_gen_docs = collection.count_documents({
    "processes.test_case_generation": {"$exists": True}
})
print(f"Documents with test_case_generation: {test_case_gen_docs}")

# Sample document with test_case_generation
sample = collection.find_one({"processes.test_case_generation": {"$exists": True}})
if sample:
    print(f"Sample session_id: {sample.get('session_id')}")
    processes = sample.get("processes", {})
    print(f"Processes type: {type(processes)}")
    print(f"Processes keys: {list(processes.keys())}")
    
    if "test_case_generation" in processes:
        tcg = processes["test_case_generation"]
        output = tcg.get("output", {})
        metadata = output.get("metadata", {})
        data = output.get("data", {})
        
        process_title = metadata.get("selected_process_title", "Unknown")
        test_case_results = data.get("test_case_results", [])
        
        print(f"Process: {process_title}, Results: {len(test_case_results)}")
        
        # Count total test cases
        total = 0
        for j, result in enumerate(test_case_results):
            test_cases = result.get("test_cases", [])
            scenario_id = result.get("scenario_id", "Unknown")
            total += len(test_cases)
            print(f"  Result {j}: Scenario {scenario_id} with {len(test_cases)} test cases")
        print(f"Total test cases: {total}")
else:
    print("No documents with test_case_generation found")
