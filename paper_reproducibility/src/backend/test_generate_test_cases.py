#!/usr/bin/env python3

import requests
import json

# Test data
test_data = {
    "selected_scenarios": [
        {
            "scenario_id": "TS_001",
            "scenario": "Verify Task Creation Functionality",
            "description": "This test scenario validates that users can create new tasks successfully",
            "objective": "Validate user ability to create new tasks",
            "category": "Functional",
            "comments": ""
        }
    ],
    "process_prompt": "Generate comprehensive test cases for the following scenario. Create detailed steps and expected results.",
    "selected_files": [
        {
            "name": "test_file.txt",
            "content": "Sample file content for testing"
        }
    ],
    "ai_model": "llama3.2:3b",
    "session_id": "eed851b0-79e7-4fef-bc11-1af2baeb075f"
}

# Make the request
url = "http://localhost:8000/api/processes/test-scenario-generation/generate-test-cases"
headers = {"Content-Type": "application/json"}

print("Testing generate-test-cases endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(test_data, indent=2)}")

try:
    response = requests.post(url, json=test_data, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ Test successful!")
    else:
        print("\n❌ Test failed!")
        
except Exception as e:
    print(f"\n❌ Request failed: {str(e)}")
