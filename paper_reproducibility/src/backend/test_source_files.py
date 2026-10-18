#!/usr/bin/env python3

from services.test_case_optimization_service import TestCaseOptimizationService
import asyncio

async def test_source_files():
    """Test source files functionality"""
    service = TestCaseOptimizationService()
    
    # Get process titles with counts (which includes source files)
    process_data = service.get_process_titles_with_counts()
    
    print("=== Process Titles with Source Files ===")
    for data in process_data:
        print(f"Process: {data['process_title']}")
        print(f"Test Cases: {data['test_case_count']}")
        print(f"Source Files: {data['source_files']}")
        print("-" * 50)
    
    # Test specific process title
    if process_data:
        test_process = process_data[0]['process_title']
        print(f"\n=== Testing specific process: {test_process} ===")
        
        source_files = service.get_source_files_for_process_title(test_process)
        print(f"Source files for '{test_process}': {source_files}")

if __name__ == "__main__":
    asyncio.run(test_source_files())
