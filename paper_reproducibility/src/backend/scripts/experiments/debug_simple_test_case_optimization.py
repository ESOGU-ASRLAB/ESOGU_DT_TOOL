#!/usr/bin/env python3

"""
Simple debug script for Test Case Optimization issue
"""

import asyncio
from services.test_case_optimization_service import TestCaseOptimizationService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simple_debug():
    """Simple debug for test case optimization"""
    
    try:
        from core.database import get_db
        db = get_db()
        collection = db["test_scenarios"]
        
        target_process = "26_son"
        
        print(f"=== Simple Search for '{target_process}' ===")
        
        # Try regex search
        docs_with_26_son = list(collection.find({
            "$or": [
                {"processes.test_scenario_generation.process_title": target_process},
                {"processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": target_process},
                {"process_title": target_process}
            ]
        }))
        
        print(f"Found {len(docs_with_26_son)} documents containing '26_son'")
        
        # If no exact match, try substring search
        if not docs_with_26_son:
            print("No exact match, trying substring search...")
            docs_with_26_son = list(collection.find({
                "$or": [
                    {"processes.test_scenario_generation.process_title": {"$regex": "26_son", "$options": "i"}},
                    {"processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": {"$regex": "26_son", "$options": "i"}},
                    {"process_title": {"$regex": "26_son", "$options": "i"}}
                ]
            }))
            print(f"Substring search found {len(docs_with_26_son)} documents")
        
        # Analyze each document
        total_test_cases = 0
        for i, doc in enumerate(docs_with_26_son):
            print(f"\n--- Document {i+1} (ID: {doc.get('_id')}) ---")
            
            processes = doc.get("processes", {})
            
            # Check test_scenario_generation
            if "test_scenario_generation" in processes:
                tsg = processes["test_scenario_generation"]
                process_title = tsg.get("process_title")
                print(f"test_scenario_generation.process_title: {process_title}")
                
                output = tsg.get("output", {})
                test_scenarios = output.get("test_scenarios", {})
                
                if isinstance(test_scenarios, dict):
                    scenarios_list = test_scenarios.get("TestScenarios", [])
                    print(f"  Found {len(scenarios_list)} scenarios in TestScenarios")
                    total_test_cases += len(scenarios_list)
                    for j, scenario in enumerate(scenarios_list[:5]):
                        print(f"    {j+1}. {scenario.get('ScenarioID', 'No ID')}: {scenario.get('Title', 'No Title')[:50]}...")
                elif isinstance(test_scenarios, list):
                    print(f"  Found {len(test_scenarios)} scenarios (direct list)")
                    total_test_cases += len(test_scenarios)
            
            # Check test_case_generation
            if "test_case_generation" in processes:
                tcg = processes["test_case_generation"]
                print(f"test_case_generation exists")
                
                output = tcg.get("output", {})
                data = output.get("data", {})
                test_case_results = data.get("test_case_results", [])
                print(f"  Found {len(test_case_results)} test_case_results")
                
                for j, result in enumerate(test_case_results):
                    metadata = result.get("metadata", {})
                    selected_process_title = metadata.get("selected_process_title")
                    if selected_process_title == target_process or target_process in str(selected_process_title):
                        print(f"    Result {j+1}: process_title={selected_process_title}, status={result.get('status')}")
                        test_cases = result.get("test_cases", [])
                        print(f"      Test cases: {len(test_cases)}")
                        total_test_cases += len(test_cases)
                        
                        # Show first few test cases
                        for k, tc in enumerate(test_cases[:3]):
                            print(f"        {k+1}. {tc.get('TestCaseID', 'No ID')}: {tc.get('Title', 'No Title')[:40]}...")
        
        print(f"\n=== Summary ===")
        print(f"Total documents found: {len(docs_with_26_son)}")
        print(f"Total test cases/scenarios found: {total_test_cases}")
        
        # Now test the service method
        print(f"\n=== Service Method Test ===")
        service = TestCaseOptimizationService()
        service_test_cases = service.get_test_cases_by_process_title(target_process)
        print(f"Service method returned: {len(service_test_cases)} test cases")
        
        if len(service_test_cases) != total_test_cases:
            print(f"MISMATCH! Expected {total_test_cases}, got {len(service_test_cases)}")
            print("This indicates the service method may not be capturing all test cases.")
        
    except Exception as e:
        print(f"Simple debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_debug())
