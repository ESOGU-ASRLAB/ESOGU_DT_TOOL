#!/usr/bin/env python3

import requests
import json

# Test data with multiple scenarios - updated for more test cases
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
    "process_prompt": """Generate comprehensive test cases for the given test scenarios. Create detailed test cases that cover different aspects including positive, negative, boundary, and edge cases.""",
    "selected_files": [
        {
            "name": "task_management.js",
            "content": """
// Task Management Application
class TaskManager {
    constructor() {
        this.tasks = [];
        this.nextId = 1;
    }
    
    createTask(title, description, dueDate, priority = 'medium') {
        if (!title || title.trim() === '') {
            throw new Error('Task title is required');
        }
        
        const task = {
            id: this.nextId++,
            title: title.trim(),
            description: description || '',
            dueDate: dueDate,
            priority: priority,
            status: 'pending',
            createdAt: new Date(),
            updatedAt: new Date()
        };
        
        this.tasks.push(task);
        return task;
    }
    
    assignTask(taskId, userId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) {
            throw new Error('Task not found');
        }
        
        task.assignedTo = userId;
        task.updatedAt = new Date();
        return task;
    }
}
            """,
            "type": "application/javascript"
        }
    ],
    "ai_model": "llama3.2:3b",
    "session_id": "eed851b0-79e7-4fef-bc11-1af2baeb075f"
}

# Make the request
url = "http://localhost:8000/api/processes/test-scenario-generation/generate-test-cases"
headers = {"Content-Type": "application/json"}

print("Testing enhanced generate-test-cases endpoint...")
print(f"URL: {url}")
print(f"Expected: 7-8 test cases per scenario")

try:
    response = requests.post(url, json=test_data, headers=headers, timeout=120)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Test successful!")
        print(f"Summary: {result.get('summary', {})}")
        
        # Check test case results
        test_case_results = result.get('test_case_results', [])
        for i, scenario_result in enumerate(test_case_results):
            print(f"\nScenario {i+1}: {scenario_result.get('scenario_title', 'Unknown')}")
            print(f"  Status: {scenario_result.get('status')}")
            print(f"  Test Cases Count: {scenario_result.get('test_cases_count', 0)}")
            
            # Show first few test case titles
            test_cases = scenario_result.get('test_cases', [])
            for j, tc in enumerate(test_cases[:3]):  # Show first 3
                print(f"    TC{j+1}: {tc.get('Title', 'No title')}")
            
            if len(test_cases) > 3:
                print(f"    ... and {len(test_cases) - 3} more test cases")
    else:
        print(f"❌ Test failed!")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")
