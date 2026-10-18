#!/usr/bin/env python3

"""
Session history debug script
"""

import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_session_history():
    """Debug session history collection"""
    
    try:
        from core.database import get_db
        db = get_db()
        collection = db["session_history"]  # Correct collection
        
        target_process = "26_son"
        
        print(f"=== Debugging Session History Collection ===")
        
        # 1. Total document count
        total_docs = collection.count_documents({})
        print(f"Total documents in session_history: {total_docs}")
        
        # 2. Find documents containing 26_son
        docs_with_26_son = list(collection.find({
            "$or": [
                {"processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": target_process},
                {"processes.test_scenario_generation.process_title": target_process}
            ]
        }))
        
        print(f"\nFound {len(docs_with_26_son)} documents with '{target_process}'")
        
        # 3. Analyze each document
        total_test_cases = 0
        for i, doc in enumerate(docs_with_26_son):
            print(f"\n--- Document {i+1} (ID: {doc.get('_id')}) ---")
            
            processes = doc.get("processes", {})
            
            # Check test_case_generation
            if "test_case_generation" in processes:
                tcg = processes["test_case_generation"]
                print(f"Has test_case_generation")
                
                output = tcg.get("output", {})
                data = output.get("data", {})
                test_case_results = data.get("test_case_results", [])
                print(f"  Found {len(test_case_results)} test_case_results")
                
                for j, result in enumerate(test_case_results):
                    metadata = result.get("metadata", {})
                    selected_process_title = metadata.get("selected_process_title")
                    if selected_process_title == target_process:
                        print(f"    Result {j+1}: process_title={selected_process_title}, status={result.get('status')}")
                        test_cases = result.get("test_cases", [])
                        print(f"      Test cases: {len(test_cases)}")
                        total_test_cases += len(test_cases)
                        
                        # Show first few test cases
                        for k, tc in enumerate(test_cases[:3]):
                            print(f"        {k+1}. {tc.get('TestCaseID', 'No ID')}: {tc.get('Title', 'No Title')[:40]}...")
                        if len(test_cases) > 3:
                            print(f"        ... and {len(test_cases) - 3} more")
            
            # Check test_scenario_generation
            if "test_scenario_generation" in processes:
                tsg = processes["test_scenario_generation"]
                process_title = tsg.get("process_title")
                if process_title == target_process:
                    print(f"Has test_scenario_generation with process_title: {process_title}")
                    
                    output = tsg.get("output", {})
                    test_scenarios = output.get("test_scenarios", {})
                    
                    if isinstance(test_scenarios, dict):
                        scenarios_list = test_scenarios.get("TestScenarios", [])
                        print(f"  Found {len(scenarios_list)} scenarios in TestScenarios")
                        total_test_cases += len(scenarios_list)
                        for j, scenario in enumerate(scenarios_list[:3]):
                            print(f"    {j+1}. {scenario.get('ScenarioID', 'No ID')}: {scenario.get('Title', 'No Title')[:40]}...")
                        if len(scenarios_list) > 3:
                            print(f"    ... and {len(scenarios_list) - 3} more")
                    elif isinstance(test_scenarios, list):
                        print(f"  Found {len(test_scenarios)} scenarios (direct list)")
                        total_test_cases += len(test_scenarios)
        
        print(f"\n=== Summary ===")
        print(f"Total documents found: {len(docs_with_26_son)}")
        print(f"Total test cases found: {total_test_cases}")
        
        # 4. Test the aggregation pipelines used by the service
        print(f"\n=== Testing Service Aggregation Pipelines ===")
        
        # Test case generation pipeline
        pipeline_test_cases = [
            {"$match": {"processes.test_case_generation.output.data.test_case_results": {"$exists": True}}},
            {"$unwind": "$processes.test_case_generation.output.data.test_case_results"},
            {"$match": {"processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": {"$ne": None, "$exists": True}}},
            {"$group": {"_id": "$processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title"}},
            {"$sort": {"_id": 1}}
        ]
        
        cursor = collection.aggregate(pipeline_test_cases)
        test_case_titles = []
        for doc in cursor:
            if doc["_id"]:
                test_case_titles.append(doc["_id"])
        
        print(f"Test case generation pipeline found {len(test_case_titles)} process titles:")
        for title in test_case_titles:
            print(f"  - {title}")
        
        # Test scenario generation pipeline
        pipeline_scenarios = [
            {"$match": {"processes.test_scenario_generation.process_title": {"$ne": None, "$exists": True}}},
            {"$group": {"_id": "$processes.test_scenario_generation.process_title"}},
            {"$sort": {"_id": 1}}
        ]
        
        cursor = collection.aggregate(pipeline_scenarios)
        scenario_titles = []
        for doc in cursor:
            if doc["_id"]:
                scenario_titles.append(doc["_id"])
        
        print(f"\nTest scenario generation pipeline found {len(scenario_titles)} process titles:")
        for title in scenario_titles:
            print(f"  - {title}")
        
        # Check if 26_son appears in multiple documents
        print(f"\n=== Checking for multiple 26_son sessions ===")
        all_26_son_docs = list(collection.find({
            "$or": [
                {"processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": target_process},
                {"processes.test_scenario_generation.process_title": target_process}
            ]
        }))
        
        print(f"Found {len(all_26_son_docs)} total documents with 26_son")
        
        for i, doc in enumerate(all_26_son_docs):
            created_at = doc.get("created_at", "Unknown")
            session_id = doc.get("session_id", "Unknown")
            print(f"  Doc {i+1}: Session {session_id}, Created: {created_at}")
            
            # Quick count of test cases in this doc
            tc_count = 0
            processes = doc.get("processes", {})
            
            if "test_case_generation" in processes:
                tcg = processes["test_case_generation"]
                output = tcg.get("output", {})
                data = output.get("data", {})
                test_case_results = data.get("test_case_results", [])
                
                for result in test_case_results:
                    metadata = result.get("metadata", {})
                    if metadata.get("selected_process_title") == target_process:
                        tc_count += len(result.get("test_cases", []))
            
            if "test_scenario_generation" in processes:
                tsg = processes["test_scenario_generation"]
                if tsg.get("process_title") == target_process:
                    output = tsg.get("output", {})
                    test_scenarios = output.get("test_scenarios", {})
                    if isinstance(test_scenarios, dict):
                        tc_count += len(test_scenarios.get("TestScenarios", []))
                    elif isinstance(test_scenarios, list):
                        tc_count += len(test_scenarios)
            
            print(f"    Test cases in this doc: {tc_count}")
        
    except Exception as e:
        print(f"Debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_session_history())
