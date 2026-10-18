#!/usr/bin/env python3
"""Test multi-process test case optimization functionality."""

from services.test_case_optimization_service import TestCaseOptimizationService

def test_process_titles_with_counts():
    """Test getting process titles with counts."""
    print("=== Testing Process Titles with Counts ===")
    
    service = TestCaseOptimizationService()
    process_data = service.get_process_titles_with_counts()
    
    print(f"Total processes: {len(process_data)}")
    
    for i, p in enumerate(process_data[:5]):  # Show first 5
        print(f"  {i+1}. {p['process_title']}: {p['test_case_count']} test cases")
    
    if len(process_data) > 5:
        print(f"  ... and {len(process_data) - 5} more processes")
    
    return process_data

def test_multi_process_test_cases():
    """Test getting test cases from multiple processes."""
    print("\n=== Testing Multi-Process Test Case Retrieval ===")
    
    service = TestCaseOptimizationService()
    
    # Get first 2 processes for testing
    process_data = service.get_process_titles_with_counts()
    if len(process_data) >= 2:
        test_processes = [p['process_title'] for p in process_data[:2]]
        print(f"Testing with processes: {test_processes}")
        
        test_cases = service.get_test_cases_by_process_titles(test_processes)
        print(f"Total test cases from {len(test_processes)} processes: {len(test_cases)}")
        
        # Group by process title
        process_groups = {}
        for tc in test_cases:
            process_title = tc.get('ProcessTitle', 'Unknown')
            if process_title not in process_groups:
                process_groups[process_title] = []
            process_groups[process_title].append(tc)
        
        print("Test cases by process:")
        for process_title, cases in process_groups.items():
            print(f"  {process_title}: {len(cases)} test cases")
    else:
        print("Not enough processes for multi-process testing")

if __name__ == "__main__":
    try:
        test_process_titles_with_counts()
        test_multi_process_test_cases()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
