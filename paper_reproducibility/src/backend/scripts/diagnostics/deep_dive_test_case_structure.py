"""
Deep Dive into Test Case Generation Structure
Analyzes the exact structure of test_case_generation process
"""

import asyncio
import json
from core.database import get_database

async def deep_dive_session(session_id: str):
    """Deep dive into session structure"""
    db = await get_database()
    collection = db["session_history"]
    
    session = await collection.find_one({"session_id": session_id})
    
    if not session:
        print(f"❌ Session not found: {session_id}")
        return
    
    processes = session.get("processes", {})
    
    if "test_case_generation" in processes:
        tcg = processes["test_case_generation"]
        
        print(f"\n{'='*80}")
        print("🔍 DEEP DIVE: test_case_generation STRUCTURE")
        print(f"{'='*80}\n")
        
        print("📦 Top-level keys in test_case_generation:")
        for key in tcg.keys():
            print(f"   - {key}")
        
        print("\n📝 Output structure:")
        output = tcg.get("output", {})
        print(f"   Output keys: {list(output.keys())}")
        
        # Check different possible structures
        print("\n🔎 Checking different data structures:")
        
        # Structure 1: output.data.test_case_results
        data = output.get("data", {})
        print(f"\n   1. output['data'] keys: {list(data.keys())}")
        test_case_results = data.get("test_case_results", [])
        print(f"      - test_case_results: {len(test_case_results)} items")
        
        # Structure 2: output.test_cases (direct)
        test_cases_direct = output.get("test_cases", [])
        print(f"\n   2. output['test_cases']: {len(test_cases_direct) if isinstance(test_cases_direct, list) else 'Not a list'}")
        
        # Structure 3: output.TestCases
        test_cases_capital = output.get("TestCases", [])
        print(f"\n   3. output['TestCases']: {len(test_cases_capital) if isinstance(test_cases_capital, list) else 'Not a list'}")
        
        # Structure 4: output.generated_test_cases
        generated = output.get("generated_test_cases", [])
        print(f"\n   4. output['generated_test_cases']: {len(generated) if isinstance(generated, list) else 'Not a list'}")
        
        # Structure 5: Check if test cases are nested under scenario
        print(f"\n   5. Checking for nested structures:")
        for key, value in output.items():
            if isinstance(value, dict):
                print(f"      - {key} (dict): {list(value.keys())[:5]}")
            elif isinstance(value, list) and len(value) > 0:
                print(f"      - {key} (list): {len(value)} items")
                if isinstance(value[0], dict):
                    print(f"         Sample item keys: {list(value[0].keys())[:5]}")
        
        # Print full output structure (first 2000 chars)
        print(f"\n{'='*80}")
        print("📄 RAW OUTPUT STRUCTURE (first 2000 chars):")
        print(f"{'='*80}")
        output_json = json.dumps(output, indent=2, default=str)
        print(output_json[:2000])
        if len(output_json) > 2000:
            print(f"\n... ({len(output_json) - 2000} more characters)")
        
        # Check metadata
        print(f"\n{'='*80}")
        print("📊 METADATA:")
        print(f"{'='*80}")
        metadata = output.get("metadata", {})
        for key, value in metadata.items():
            print(f"   {key}: {value}")

async def main():
    session_id = "project.xml Test Scenario&Test Cases"
    await deep_dive_session(session_id)

if __name__ == "__main__":
    asyncio.run(main())
