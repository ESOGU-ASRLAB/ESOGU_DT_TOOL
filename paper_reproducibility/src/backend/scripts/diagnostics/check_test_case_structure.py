from core.database import get_database
import asyncio

async def check_test_case_structure():
    db = await get_database()
    collection = db['session_history']
    
    # Find documents with more test cases
    pipeline = [
        {"$match": {"processes.test_case_generation.output.metadata.total_test_cases": {"$exists": True}}},
        {"$project": {
            "session_id": 1,
            "total_test_cases": "$processes.test_case_generation.output.metadata.total_test_cases",
            "selected_process_title": "$processes.test_case_generation.output.metadata.selected_process_title",
            "test_case_results": "$processes.test_case_generation.output.test_case_results"
        }},
        {"$sort": {"total_test_cases": -1}}
    ]
    
    results = await collection.aggregate(pipeline).to_list(length=10)
    
    print("Top 10 sessions with most test cases:")
    for result in results:
        session_id = result.get('session_id', 'Unknown')
        total = result.get('total_test_cases', 0)
        process_title = result.get('selected_process_title', 'N/A')
        test_case_results = result.get('test_case_results', [])
        
        actual_total = 0
        for tcr in test_case_results:
            if tcr.get('status') == 'success':
                actual_total += len(tcr.get('test_cases', []))
        
        print(f"Session: {session_id}, Metadata Total: {total}, Actual Total: {actual_total}, Process: {process_title}")
    
    # Find the session with 56 test cases specifically
    doc_with_many = await collection.find_one({
        "processes.test_case_generation.output.metadata.total_test_cases": {"$gte": 50}
    })
    
    if doc_with_many:
        print(f"\nAnalyzing session with many test cases:")
        test_case_gen = doc_with_many.get('processes', {}).get('test_case_generation', {})
        output = test_case_gen.get('output', {})
        results = output.get('test_case_results', [])
        metadata = output.get('metadata', {})
        
        print(f"Session ID: {doc_with_many.get('session_id')}")
        print(f"Metadata total: {metadata.get('total_test_cases')}")
        print(f"Selected process title: {metadata.get('selected_process_title')}")
        print(f"Number of scenario results: {len(results)}")
        
        total_actual = 0
        for i, result in enumerate(results):
            scenario_id = result.get('scenario_id', 'Unknown')
            status = result.get('status', 'Unknown')
            test_cases = result.get('test_cases', [])
            print(f"  Scenario {i+1} ({scenario_id}): {len(test_cases)} test cases, status: {status}")
            if status == 'success':
                total_actual += len(test_cases)
        
        print(f"Total actual test cases: {total_actual}")
        
        # Show structure of first test case from first successful scenario
        for result in results:
            if result.get('status') == 'success' and result.get('test_cases'):
                first_tc = result['test_cases'][0]
                print(f"First test case structure: {list(first_tc.keys())}")
                print(f"First test case sample:")
                for key, value in first_tc.items():
                    print(f"  {key}: {str(value)[:100]}...")
                break

if __name__ == "__main__":
    asyncio.run(check_test_case_structure())
