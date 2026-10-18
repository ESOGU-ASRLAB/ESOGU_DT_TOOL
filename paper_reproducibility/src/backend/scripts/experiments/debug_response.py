#!/usr/bin/env python3

import requests
import json

# Simpler test to check raw response
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
            print("=" * 50)
            print(raw_response)
            print("=" * 50)
            
            # Try to find JSON manually
            import re
            json_pattern = r'\{[\s\S]*?"TestCases"[\s\S]*?\][\s\S]*?\}'
            json_match = re.search(json_pattern, raw_response)
            if json_match:
                print("Found JSON pattern:")
                print(json_match.group(0)[:500] + "...")
            else:
                print("No JSON pattern found in response")
                
except Exception as e:
    print(f"Error: {e}")
