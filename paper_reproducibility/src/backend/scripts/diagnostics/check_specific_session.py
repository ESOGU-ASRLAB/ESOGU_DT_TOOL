from core.database import get_db

db = get_db()
collection = db["session_history"]

# Look for the specific session_id from the user's request
target_session_id = "a73c8ab2-cd5d-45be-84c5-b32d71fde91e"

print(f"=== Checking Session {target_session_id} ===")

doc = collection.find_one({"session_id": target_session_id})
if doc:
    print("Found the document!")
    
    processes = doc.get("processes", {})
    print(f"Processes keys: {list(processes.keys())}")
    
    if "test_case_generation" in processes:
        tcg = processes["test_case_generation"]
        output = tcg.get("output", {})
        data = output.get("data", {})
        
        test_case_results = data.get("test_case_results", [])
        print(f"Number of test_case_results: {len(test_case_results)}")
        
        total_test_cases = 0
        for i, result in enumerate(test_case_results):
            scenario_id = result.get("scenario_id", "Unknown")
            test_cases = result.get("test_cases", [])
            metadata = result.get("metadata", {})
            process_title = metadata.get("selected_process_title", "Unknown")
            
            print(f"  Result {i}: Scenario {scenario_id}")
            print(f"    Process title: {process_title}")
            print(f"    Test cases: {len(test_cases)}")
            
            total_test_cases += len(test_cases)
            
            # Show first test case
            if test_cases:
                first_tc = test_cases[0]
                print(f"    First test case: {first_tc.get('TestCaseID')} - {first_tc.get('Title', 'No Title')}")
        
        print(f"\nTOTAL TEST CASES: {total_test_cases}")
    else:
        print("No test_case_generation found in processes")
else:
    print("Document not found!")
    
    # Let's find any document with 26_son
    print("\n=== Looking for any document with 26_son ===")
    doc_with_26_son = collection.find_one({
        "processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": "26_son"
    })
    
    if doc_with_26_son:
        print(f"Found document with 26_son: {doc_with_26_son.get('session_id')}")
        
        processes = doc_with_26_son.get("processes", {})
        if "test_case_generation" in processes:
            tcg = processes["test_case_generation"]
            output = tcg.get("output", {})
            data = output.get("data", {})
            
            test_case_results = data.get("test_case_results", [])
            print(f"Number of test_case_results: {len(test_case_results)}")
            
            total_test_cases = 0
            for i, result in enumerate(test_case_results):
                scenario_id = result.get("scenario_id", "Unknown")
                test_cases = result.get("test_cases", [])
                metadata = result.get("metadata", {})
                process_title = metadata.get("selected_process_title", "Unknown")
                
                print(f"  Result {i}: Scenario {scenario_id}, Process: {process_title}, Test cases: {len(test_cases)}")
                total_test_cases += len(test_cases)
            
            print(f"TOTAL TEST CASES: {total_test_cases}")
    else:
        print("No document found with 26_son either")
