#!/usr/bin/env python3

import requests
import json

# Test data with multiple scenarios (similar to frontend)
test_data = {
    "selected_scenarios": [
        {
            "scenario_id": "TS_001",
            "scenario": "Verify Task Creation Functionality",
            "description": "This test scenario validates that users can create new tasks successfully",
            "objective": "Validate user ability to create new tasks",
            "category": "Functional",
            "comments": ""
        },
        {
            "scenario_id": "TS_002",
            "scenario": "Test Task Assignment Functionality",
            "description": "This test scenario assesses that users can assign tasks to team members correctly",
            "objective": "Validate user ability to assign tasks to team members",
            "category": "Functional",
            "comments": ""
        }
    ],
    "process_prompt": """Generate comprehensive test cases for the given test scenarios. Return ONLY a valid JSON object with the following structure:

{
  "TestCases": [
    {
      "ScenarioID": "ID of the scenario this test case belongs to",
      "TestCaseID": "Unique test case identifier",
      "Title": "Clear and descriptive test case title",
      "Description": "Detailed description of the test case",
      "Objective": "What this test case aims to verify",
      "Category": "Functional/Non-Functional/Security/etc.",
      "Comments": "Additional notes"
    }
  ]
}""",
    "selected_files": [
        {
            "name": "sample_code.js",
            "content": "// Sample application code\nfunction createTask(title, description) {\n  return { id: Date.now(), title, description, status: 'pending' };\n}\n\nfunction assignTask(taskId, userId) {\n  // Assignment logic\n  return { taskId, userId, assignedAt: new Date() };\n}",
            "type": "application/javascript"
        }
    ],
    "ai_model": "llama3.2:3b",
    "session_id": "eed851b0-79e7-4fef-bc11-1af2baeb075f"
}

# Make the request
url = "http://localhost:8000/api/processes/test-scenario-generation/generate-test-cases"
headers = {"Content-Type": "application/json"}

print("Testing generate-test-cases endpoint with multiple scenarios...")
print(f"URL: {url}")
print(f"Number of scenarios: {len(test_data['selected_scenarios'])}")
print(f"AI Model: {test_data['ai_model']}")

try:
    response = requests.post(url, json=test_data, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Test successful!")
        print(f"Summary: {result.get('summary', {})}")
        print(f"Number of results: {len(result.get('test_case_results', []))}")
        
        # Print first result details
        if result.get('test_case_results'):
            first_result = result['test_case_results'][0]
            print(f"First result status: {first_result.get('status')}")
            print(f"First result test cases count: {first_result.get('test_cases_count', 0)}")
    else:
        print(f"❌ Test failed!")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")
