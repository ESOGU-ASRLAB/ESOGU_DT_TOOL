#!/usr/bin/env python3

"""
Process titles debug script
"""

import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_process_titles():
    """Debug process titles aggregation"""
    
    try:
        from core.database import get_db
        db = get_db()
        collection = db["test_scenarios"]
        
        target_process = "26_son"
        
        print(f"=== Debugging Process Titles Aggregation ===")
        
        # 1. Test the first pipeline (test_case_generation)
        print("1. Testing test_case_generation pipeline...")
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
                if doc["_id"] == target_process:
                    print(f"  Found '{target_process}' in test_case_generation!")
        
        print(f"  Found {len(test_case_titles)} process titles from test_case_generation")
        print(f"  Titles: {test_case_titles}")
        
        # 2. Test the second pipeline (test_scenario_generation)
        print("\n2. Testing test_scenario_generation pipeline...")
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
                if doc["_id"] == target_process:
                    print(f"  Found '{target_process}' in test_scenario_generation!")
        
        print(f"  Found {len(scenario_titles)} process titles from test_scenario_generation")
        print(f"  Titles: {scenario_titles}")
        
        # 3. Combined results
        all_titles = set(test_case_titles + scenario_titles)
        print(f"\n3. Combined results: {len(all_titles)} unique process titles")
        print(f"   Combined: {sorted(list(all_titles))}")
        
        if target_process in all_titles:
            print(f"\n'{target_process}' found in aggregation results!")
            
            # Now debug why get_test_cases_by_process_title might be finding different data
            print(f"\n=== Debugging get_test_cases_by_process_title for '{target_process}' ===")
            
            # Check test_case_generation documents
            print("Checking test_case_generation documents...")
            docs = list(collection.find(
                {"processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": target_process},
                {"processes.test_case_generation": 1}
            ))
            print(f"Found {len(docs)} documents in test_case_generation with '{target_process}'")
            
            total_test_cases = 0
            for i, doc in enumerate(docs):
                test_case_gen_data = doc.get("processes", {}).get("test_case_generation", {})
                output_data = test_case_gen_data.get("output", {}).get("data", {})
                test_case_results = output_data.get("test_case_results", [])
                
                print(f"  Doc {i+1}: {len(test_case_results)} test_case_results")
                
                for j, result in enumerate(test_case_results):
                    metadata = result.get("metadata", {})
                    if metadata.get("selected_process_title") == target_process:
                        test_cases = result.get("test_cases", [])
                        print(f"    Result {j+1}: {len(test_cases)} test cases")
                        total_test_cases += len(test_cases)
                        
                        # Show test cases
                        for k, tc in enumerate(test_cases[:3]):
                            print(f"      {k+1}. {tc.get('TestCaseID', 'No ID')}: {tc.get('Title', 'No Title')[:40]}...")
            
            # Check test_scenario_generation documents
            print(f"\nChecking test_scenario_generation documents...")
            docs = list(collection.find(
                {"processes.test_scenario_generation.process_title": target_process},
                {"processes.test_scenario_generation": 1}
            ))
            print(f"Found {len(docs)} documents in test_scenario_generation with '{target_process}'")
            
            for i, doc in enumerate(docs):
                test_generation_data = doc.get("processes", {}).get("test_scenario_generation", {})
                test_scenarios = test_generation_data.get("output", {}).get("test_scenarios", {})
                
                scenarios_list = []
                if isinstance(test_scenarios, dict):
                    scenarios_list = test_scenarios.get("TestScenarios", [])
                elif isinstance(test_scenarios, list):
                    scenarios_list = test_scenarios
                
                print(f"  Doc {i+1}: {len(scenarios_list)} scenarios")
                total_test_cases += len(scenarios_list)
                
                for j, scenario in enumerate(scenarios_list[:3]):
                    print(f"    {j+1}. {scenario.get('ScenarioID', 'No ID')}: {scenario.get('Title', 'No Title')[:40]}...")
            
            print(f"\nTotal test cases found in database: {total_test_cases}")
        else:
            print(f"\n'{target_process}' NOT found in aggregation results!")
        
    except Exception as e:
        print(f"Debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_process_titles())
