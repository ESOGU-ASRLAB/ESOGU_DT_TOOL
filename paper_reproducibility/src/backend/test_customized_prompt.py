#!/usr/bin/env python3

import requests
import json

# Test with a more comprehensive, customized prompt (like frontend would send)
test_data = {
    "selected_scenarios": [
        {
            "scenario_id": "TS_001",
            "scenario": "Verify Task Creation Functionality",
            "description": "This test scenario validates that users can create new tasks successfully",
            "objective": "Validate user ability to create new tasks",
            "category": "Functional"
        }
    ],
    "process_prompt": """Create comprehensive test cases for software testing. Focus on generating detailed, executable test cases that cover various testing aspects including positive, negative, boundary, and edge case scenarios.

For each test scenario provided, generate multiple test cases that thoroughly validate the functionality. Each test case should include:
- Clear test case ID and title
- Detailed description of what is being tested
- Specific objective of the test
- Test category (Positive, Negative, Boundary, etc.)
- Additional comments or notes

Ensure test cases are:
1. Comprehensive and cover different testing aspects
2. Focused on the specific scenario objectives
3. Include both happy path and error scenarios
4. Consider edge cases and boundary conditions

JSON Output Structure:

{
    "TestCases": [
        {
            "ScenarioID": "<Dynamic Scenario ID>",
            "TestCaseID": "<Dynamic Test Case ID>",
            "Title": "<Test Case Title>",
            "Description": "<Detailed test case description>",
            "Objective": "<Objective of the test case>",
            "Category": "<Test Category>",
            "Comments": "<Additional notes>"
        }
    ]
}""",
    "selected_files": [
        {
            "name": "task_manager.js",
            "content": """
// Task Manager Application
class TaskManager {
    constructor() {
        this.tasks = [];
        this.nextId = 1;
    }
    
    createTask(title, description, priority = 'medium', dueDate = null) {
        // Validation
        if (!title || title.trim() === '') {
            throw new Error('Task title is required');
        }
        
        if (title.length > 255) {
            throw new Error('Task title too long');
        }
        
        const task = {
            id: this.nextId++,
            title: title.trim(),
            description: description || '',
            priority: priority,
            dueDate: dueDate,
            status: 'pending',
            createdAt: new Date(),
            updatedAt: new Date()
        };
        
        this.tasks.push(task);
        return task;
    }
    
    getTasks() {
        return this.tasks;
    }
    
    deleteTask(taskId) {
        const index = this.tasks.findIndex(t => t.id === taskId);
        if (index === -1) {
            throw new Error('Task not found');
        }
        return this.tasks.splice(index, 1)[0];
    }
}
            """,
            "type": "application/javascript"
        }
    ],
    "ai_model": "llama3.2:3b",
    "session_id": "test-enhanced-prompt"
}

# Make the request
url = "http://localhost:8000/api/processes/test-scenario-generation/generate-test-cases"
headers = {"Content-Type": "application/json"}

print("Testing with comprehensive customized process prompt...")
print(f"Process prompt length: {len(test_data['process_prompt'])} characters")

try:
    response = requests.post(url, json=test_data, headers=headers, timeout=180)
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
            
            # Show test case details
            test_cases = scenario_result.get('test_cases', [])
            for j, tc in enumerate(test_cases[:5]):  # Show first 5
                print(f"    TC{j+1}: {tc.get('TestCaseID', 'No ID')} - {tc.get('Title', 'No title')}")
                print(f"         Category: {tc.get('Category', 'Unknown')} | Steps: {len(tc.get('TestSteps', []))}")
            
            if len(test_cases) > 5:
                print(f"    ... and {len(test_cases) - 5} more test cases")
                
            # Show a snippet of raw response to see if our prompt is being used
            raw_response = scenario_result.get('raw_response', '')
            if raw_response:
                print(f"\n  Raw Response Preview (first 200 chars):")
                print(f"    {raw_response[:200]}...")
    else:
        print(f"❌ Test failed!")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")
