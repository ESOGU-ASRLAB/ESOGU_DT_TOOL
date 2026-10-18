from core.database import get_db

def check_process_titles_with_test_cases():
    db = get_db()
    collection = db['environment_setup_sessions']

    # Find all documents that have test_case_generation data
    docs_with_test_cases = collection.find({
        'processes.test_case_generation.output.data.test_case_results': {'$exists': True, '$ne': None}
    })

    print('=== Process Titles with Test Cases Generated ===')
    for doc in docs_with_test_cases:
        for process in doc.get('processes', []):
            if 'test_case_generation' in process and process['test_case_generation'].get('output', {}).get('data', {}).get('test_case_results'):
                process_title = process['test_case_generation']['output']['metadata']['selected_process_title']
                test_case_results = process['test_case_generation']['output']['data']['test_case_results']
                
                print(f'\n  Process: {process_title}')
                print(f'  Number of test_case_results entries: {len(test_case_results)}')
                
                # Count total test cases across all entries
                total_test_cases = 0
                for i, result in enumerate(test_case_results):
                    test_cases = result.get('test_cases', [])
                    total_test_cases += len(test_cases)
                    print(f'    Entry {i+1}: {len(test_cases)} test cases')
                
                print(f'  TOTAL TEST CASES: {total_test_cases}')

if __name__ == "__main__":
    check_process_titles_with_test_cases()
