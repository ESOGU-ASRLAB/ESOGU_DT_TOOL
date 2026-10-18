#!/usr/bin/env python3

"""
Enhanced debug script for Test Case Optimization issue
"""

import asyncio
from services.test_case_optimization_service import TestCaseOptimizationService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def enhanced_debug():
    """Enhanced debug for test case optimization"""
    
    try:
        from core.database import get_db
        db = get_db()
        collection = db["test_scenarios"]
        
        target_process = "26_son"
        
        print(f"=== Enhanced Search for '{target_process}' ===")
        
        # 1. Search all documents containing "26_son" anywhere
        print("1. Searching all documents containing '26_son'...")
        docs_with_26_son = list(collection.find({"$text": {"$search": "26_son"}}))
        if not docs_with_26_son:
            # Try regex search if text search fails
            docs_with_26_son = list(collection.find({
                "$or": [
                    {"processes.test_scenario_generation.process_title": {"$regex": "26_son", "$options": "i"}},
                    {"processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": {"$regex": "26_son", "$options": "i"}},
                    {"process_title": {"$regex": "26_son", "$options": "i"}}
                ]
            }))
        
        print(f"Found {len(docs_with_26_son)} documents containing '26_son'")
        
        # 2. Find the exact structure
        for i, doc in enumerate(docs_with_26_son):
            print(f"\n--- Document {i+1} ---")
            print(f"Document ID: {doc.get('_id')}")
            
            # Check different possible structures
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
                    for j, scenario in enumerate(scenarios_list[:3]):
                        print(f"    {j+1}. {scenario.get('ScenarioID')}: {scenario.get('Title', 'No Title')[:50]}...")
                elif isinstance(test_scenarios, list):
                    print(f"  Found {len(test_scenarios)} scenarios (direct list)")
            
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
                    print(f"    Result {j+1}: process_title={selected_process_title}, status={result.get('status')}")
                    test_cases = result.get("test_cases", [])
                    print(f"      Test cases: {len(test_cases)}")
            
            # Check for direct process_title field
            if "process_title" in doc:
                print(f"Direct process_title: {doc['process_title']}")
        
        # 3. Try to find any documents with multiple test cases
        print(f"\n=== Looking for documents with many test cases ===")
        
        # Aggregate to find documents with most test cases
        pipeline = [
            {"$match": {
                "$or": [
                    {"processes.test_scenario_generation.process_title": {"$exists": True}},
                    {"processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": {"$exists": True}}
                ]
            }},
            {"$project": {
                "process_title_tsg": "$processes.test_scenario_generation.process_title",
                "test_case_results": "$processes.test_case_generation.output.data.test_case_results",
                "scenarios": "$processes.test_scenario_generation.output.test_scenarios.TestScenarios"
            }}
        ]
        
        aggregation_results = list(collection.aggregate(pipeline))
        print(f"Found {len(aggregation_results)} documents with process titles")
        
        # Look for 26_son specifically
        for doc in aggregation_results:
            process_title_tsg = doc.get("process_title_tsg")
            test_case_results = doc.get("test_case_results", [])
            scenarios = doc.get("scenarios", [])
            
            if process_title_tsg == "26_son":
                print(f"\nFound 26_son in test_scenario_generation:")
                print(f"  Scenarios: {len(scenarios) if scenarios else 0}")
                
            # Check test_case_results
            for result in test_case_results:
                metadata = result.get("metadata", {})
                if metadata.get("selected_process_title") == "26_son":
                    print(f"\nFound 26_son in test_case_generation:")
                    print(f"  Test cases in this result: {len(result.get('test_cases', []))}")
        
    except Exception as e:
        print(f"Enhanced debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(enhanced_debug())
