"""
Check exact format of test_case_generation data in database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
import json
from datetime import datetime

async def check_test_case_format():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["stlc_database"]
    collection = db["session_history"]
    
    print("=" * 70)
    print("SEARCHING FOR TEST CASE GENERATION DATA")
    print("=" * 70)
    
    # Find sessions with test_case_generation
    sessions = await collection.find({
        "process_data.test_case_generation": {"$exists": True}
    }).to_list(length=None)
    
    print(f"\n✅ Found {len(sessions)} sessions with test_case_generation\n")
    
    for idx, session in enumerate(sessions, 1):
        print(f"\n{'=' * 70}")
        print(f"SESSION {idx}: {session.get('session_name', 'Unknown')}")
        print(f"{'=' * 70}")
        
        process_data = session.get("process_data", {})
        tc_gen = process_data.get("test_case_generation", {})
        
        print(f"\n📋 test_case_generation structure:")
        print(f"   Top-level keys: {list(tc_gen.keys())}")
        
        # Check for output
        if "output" in tc_gen:
            output = tc_gen["output"]
            print(f"\n   output type: {type(output)}")
            print(f"   output keys: {list(output.keys()) if isinstance(output, dict) else 'Not a dict'}")
            
            # Check for data
            if isinstance(output, dict) and "data" in output:
                data = output["data"]
                print(f"\n   output.data type: {type(data)}")
                print(f"   output.data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Check for test_case_results
                if isinstance(data, dict) and "test_case_results" in data:
                    test_case_results = data["test_case_results"]
                    print(f"\n   output.data.test_case_results type: {type(test_case_results)}")
                    if isinstance(test_case_results, list) and len(test_case_results) > 0:
                        print(f"   output.data.test_case_results length: {len(test_case_results)}")
                        print(f"   First item keys: {list(test_case_results[0].keys())}")
                        
                        # Check for test_cases in first result
                        if "test_cases" in test_case_results[0]:
                            test_cases = test_case_results[0]["test_cases"]
                            print(f"\n   output.data.test_case_results[0].test_cases length: {len(test_cases)}")
                            if len(test_cases) > 0:
                                print(f"\n   📝 Sample test case:")
                                sample = test_cases[0]
                                print(f"      Keys: {list(sample.keys())}")
                                print(f"      test_case_id: {sample.get('test_case_id', 'N/A')}")
                                print(f"      test_scenario_id: {sample.get('test_scenario_id', 'N/A')}")
                                print(f"      test_type: {sample.get('test_type', 'N/A')}")
                                print(f"      Has steps: {bool(sample.get('test_steps'))}")
                                print(f"      Has test_data: {bool(sample.get('test_data'))}")
                                print(f"      Has expected_results: {bool(sample.get('expected_results'))}")
            
            # Check for old format (direct test_cases)
            if isinstance(output, dict) and "test_cases" in output:
                test_cases = output["test_cases"]
                print(f"\n   ⚠️  OLD FORMAT DETECTED!")
                print(f"   output.test_cases length: {len(test_cases)}")
                if len(test_cases) > 0:
                    print(f"   First test case keys: {list(test_cases[0].keys())}")
        
        # Save full structure to JSON for one session
        if idx == 1:
            sample_file = "test_case_generation_sample_structure.json"
            with open(sample_file, "w", encoding="utf-8") as f:
                # Convert datetime objects to strings
                session_copy = json.loads(json.dumps(session, default=str))
                json.dump(session_copy.get("process_data", {}).get("test_case_generation", {}), f, indent=2, ensure_ascii=False)
            print(f"\n   💾 Full structure saved to: {sample_file}")

    client.close()

if __name__ == "__main__":
    asyncio.run(check_test_case_format())
