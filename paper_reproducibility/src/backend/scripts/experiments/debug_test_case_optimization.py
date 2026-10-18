#!/usr/bin/env python3

"""
Debug script for Test Case Optimization issue
"""

import asyncio
from services.test_case_optimization_service import TestCaseOptimizationService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_test_case_optimization():
    """Debug test case optimization service"""
    
    service = TestCaseOptimizationService()
    
    # 1. Get all process titles
    print("=== Available Process Titles ===")
    process_titles = service.get_available_process_titles()
    print(f"Found {len(process_titles)} process titles:")
    for title in process_titles:
        print(f"  - {title}")
    
    # 2. Focus on 26_son
    target_process = "26_son"
    print(f"\n=== Test Cases for '{target_process}' ===")
    
    if target_process in process_titles:
        test_cases = service.get_test_cases_by_process_title(target_process)
        print(f"Found {len(test_cases)} test cases for '{target_process}':")
        
        # Group by ScenarioID to understand structure
        scenario_groups = {}
        for tc in test_cases:
            scenario_id = tc.get("ScenarioID", "Unknown")
            if scenario_id not in scenario_groups:
                scenario_groups[scenario_id] = []
            scenario_groups[scenario_id].append(tc)
        
        print(f"Grouped into {len(scenario_groups)} scenarios:")
        for scenario_id, cases in scenario_groups.items():
            print(f"  Scenario {scenario_id}: {len(cases)} test cases")
            for i, case in enumerate(cases[:3]):  # Show first 3 cases per scenario
                print(f"    {i+1}. {case.get('TestCaseID', 'No ID')}: {case.get('Title', 'No Title')[:60]}...")
            if len(cases) > 3:
                print(f"    ... and {len(cases) - 3} more")
    else:
        print(f"Process title '{target_process}' not found!")
    
    # 3. Check database structure
    print(f"\n=== Database Structure Analysis ===")
    try:
        from core.database import get_db
        db = get_db()
        collection = db["session_history"]  # CORRECT collection!
        
        # Try different search patterns for 26_son
        patterns = [
            {"processes.test_case_generation.selected_process_title": target_process},  # CORRECT path
            {"processes.test_case_generation.output.metadata.selected_process_title": target_process},
            {"processes.test_scenario_generation.process_title": target_process},
            {"processes.test_case_generation.metadata.selected_process_title": target_process},
            {"processes.test_scenario_generation.metadata.selected_process_title": target_process}, 
        ]
        
        found_doc = None
        for pattern in patterns:
            docs = list(collection.find(pattern).limit(1))
            if docs:
                print(f"Found {len(docs)} documents with pattern: {pattern}")
                found_doc = docs[0]
                break
                
        # If still nothing, search more broadly
        if not found_doc:
            print("Trying broader search...")
            # Look for ANY document with test_case_generation
            broad_docs = list(collection.find({"processes.test_case_generation": {"$exists": True}}).limit(3))
            print(f"Found {len(broad_docs)} documents with any test_case_generation")
            
            for i, doc in enumerate(broad_docs):
                session_id = doc.get("session_id", "unknown")
                print(f"  Doc {i+1}: session_id = {session_id}")
                
                # Check if this document has our target process
                processes = doc.get("processes", {})
                tcg = processes.get("test_case_generation", {})
                if isinstance(tcg, dict):
                    output = tcg.get("output", {})
                    if isinstance(output, dict) and "data" in output:
                        data = output["data"]
                        if isinstance(data, dict) and "test_case_results" in data:
                            results = data["test_case_results"]
                            for result in results:
                                if isinstance(result, dict):
                                    metadata = result.get("metadata", {})
                                    process_title = metadata.get("selected_process_title")
                                    if process_title == target_process:
                                        print(f"    FOUND '{target_process}' in this document!")
                                        found_doc = doc
                                        break
                if found_doc:
                    break
                    
        # Analyze the structure if we found a document
        if found_doc:
            print(f"\n=== Analyzing Document with '{target_process}' ===")
            processes = found_doc.get("processes", {})
            
            # Check test_case_generation structure
            if "test_case_generation" in processes:
                tcg = processes["test_case_generation"]
                output = tcg.get("output", {})
                test_case_results = output.get("test_case_results", [])  # Correct path: no "data" level
                
                print(f"Found {len(test_case_results)} test_case_results")
                
                total_test_cases = 0
                for i, result in enumerate(test_case_results):
                    test_cases_count = len(result.get('test_cases', []))
                    scenario_id = result.get('scenario_id', 'Unknown')
                    total_test_cases += test_cases_count
                    print(f"  Result {i+1} (Scenario {scenario_id}): {test_cases_count} test cases")
                        
                print(f"TOTAL TEST CASES for '{target_process}': {total_test_cases}")
            else:
                print("No test_case_generation found in document")
        else:
            print(f"No document found containing '{target_process}'")
                
    except Exception as e:
        print(f"Database analysis error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(debug_test_case_optimization())
