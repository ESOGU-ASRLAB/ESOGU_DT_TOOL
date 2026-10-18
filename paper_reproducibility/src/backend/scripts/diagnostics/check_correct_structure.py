from core.database import get_db
import json

db = get_db()
collection = db["session_history"]

# Look for the specific session_id from the user's request
target_session_id = "a73c8ab2-cd5d-45be-84c5-b32d71fde91e"

print(f"=== Checking Correct Structure for {target_session_id} ===")

doc = collection.find_one({"session_id": target_session_id})
if doc:
    processes = doc.get("processes", {})
    
    if "test_case_generation" in processes:
        tcg = processes["test_case_generation"]
        output = tcg.get("output", {})
        
        # Check if test_case_results is directly under output
        test_case_results = output.get("test_case_results", [])
        print(f"test_case_results (direct): {len(test_case_results)}")
        
        if len(test_case_results) > 0:
            print(f"Found {len(test_case_results)} test_case_results!")
            
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
                    print(f"    First test case: {first_tc.get('TestCaseID')} - {first_tc.get('Title', 'No Title')[:50]}...")
            
            print(f"\nTOTAL TEST CASES: {total_test_cases}")
        else:
            print("No test_case_results found")
            print(f"Output keys: {list(output.keys())}")
            print(f"Output content sample: {json.dumps(output, indent=2, default=str)[:1000]}...")
