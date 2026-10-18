#!/usr/bin/env python3

import requests
import json
import re

# Test the full flow
test_data = {
    "selected_scenarios": [
        {
            "scenario_id": "TS_001",
            "scenario": "Verify Task Creation",
            "description": "Test task creation functionality",
            "objective": "Validate task creation",
            "category": "Functional"
        }
    ],
    "process_prompt": "Generate test cases",
    "selected_files": [
        {
            "name": "test.js",
            "content": "function createTask() { return true; }"
        }
    ],
    "ai_model": "llama3.2:3b",
    "session_id": "test-session"
}

try:
    response = requests.post(
        "http://localhost:8000/api/processes/test-scenario-generation/generate-test-cases",
        json=test_data,
        headers={"Content-Type": "application/json"},
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        test_case_results = result.get('test_case_results', [])
        if test_case_results:
            raw_response = test_case_results[0].get('raw_response', '')
            print("Raw LLM Response:")
            print("=" * 80)
            print(raw_response)
            print("=" * 80)
            
            # Test our parsing logic
            pattern = r'\*\*Test Case \d+:([^\*]+?)\*\*(?:\s*\n)?(.*?)(?=\*\*Test Case \d+:|$)'
            matches = re.findall(pattern, raw_response, re.DOTALL)
            print(f"\nRegex matches found: {len(matches)}")
            
            for i, (title, content) in enumerate(matches):
                print(f"\nMatch {i+1}:")
                print(f"  Title: {title.strip()}")
                print(f"  Content preview: {content[:100]}...")
                
            # Test actual parsed results
            parsed_test_cases = test_case_results[0].get('test_cases', [])
            print(f"\nActual parsed test cases: {len(parsed_test_cases)}")
            for i, tc in enumerate(parsed_test_cases):
                print(f"  TC {i+1}: {tc.get('Title', 'No title')} (ID: {tc.get('TestCaseID', 'No ID')})")
                print(f"         Steps: {len(tc.get('TestSteps', []))} | Prerequisites: {len(tc.get('Prerequisites', []))}")
                
except Exception as e:
    print(f"Error: {e}")
