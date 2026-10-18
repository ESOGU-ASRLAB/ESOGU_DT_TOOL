from core.database import get_db

def check_all_process_data():
    db = get_db()
    collection = db['environment_setup_sessions']

    print('=== Checking ALL process data ===')
    
    # Check all documents
    docs = collection.find({})
    doc_count = 0
    
    for doc in docs:
        doc_count += 1
        print(f'\nDocument {doc_count}:')
        
        processes = doc.get('processes', [])
        print(f'  Number of processes: {len(processes)}')
        
        for i, process in enumerate(processes):
            print(f'  Process {i+1}:')
            
            # Check test_scenario_generation
            if 'test_scenario_generation' in process:
                tsg = process['test_scenario_generation']
                if 'output' in tsg and 'metadata' in tsg['output']:
                    process_title = tsg['output']['metadata'].get('selected_process_title', 'Unknown')
                    scenarios = tsg['output'].get('data', {}).get('test_scenarios', [])
                    print(f'    Test Scenario Generation: {process_title} ({len(scenarios)} scenarios)')
            
            # Check test_case_generation
            if 'test_case_generation' in process:
                tcg = process['test_case_generation']
                if 'output' in tcg and 'metadata' in tcg['output']:
                    process_title = tcg['output']['metadata'].get('selected_process_title', 'Unknown')
                    test_case_results = tcg['output'].get('data', {}).get('test_case_results', [])
                    print(f'    Test Case Generation: {process_title} ({len(test_case_results)} test case results)')
                    
                    # Count total test cases
                    total_test_cases = 0
                    for result in test_case_results:
                        test_cases = result.get('test_cases', [])
                        total_test_cases += len(test_cases)
                    print(f'      Total test cases: {total_test_cases}')
    
    print(f'\nTotal documents: {doc_count}')

if __name__ == "__main__":
    check_all_process_data()
