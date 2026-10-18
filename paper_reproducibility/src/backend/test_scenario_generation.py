#!/usr/bin/env python3

import requests
import json
import time

# Test the test scenario generation endpoint using /run (FormData)
url = "http://localhost:8000/api/processes/test-scenario-generation/run"

# Create FormData
form_data = {
    'final_prompt': """Generate comprehensive test scenarios for Integration Testing under Functional category.

## TASK SPECIFICATION
Generate test scenarios for **Integration Testing** testing under **Functional** category.

## REQUIREMENTS TO CONSIDER
### Scoring Elements:
• Clear test objective: Ensure each scenario has a well-defined, specific objective
• Detailed test steps: Provide comprehensive, step-by-step test procedures
• Expected results: Define clear, measurable expected outcomes

### Testing Instructions:
• Define test preconditions: Establish necessary conditions before test execution
• Include validation steps: Add verification steps to confirm test success

Generate test scenarios now following the exact JSON structure above.""",
    'model': 'llama3.2:3b',
    'test_type': 'Integration Testing',
    'test_category': 'Functional',
    'session_id': 'test_session_' + str(int(time.time() * 1000)),
    'process_title': 'Test User Authentication Integration'
}

print("Testing test scenario generation endpoint (/run)...")
print(f"URL: {url}")
print(f"Model: {form_data['model']}")
print(f"Session ID: {form_data['session_id']}")
print(f"Process Title: {form_data['process_title']}")

try:
    response = requests.post(url, data=form_data)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Test successful!")
        print(f"Status: {result.get('status')}")
        
        # Check for test scenarios in the response
        content = result.get('content', '')
        if 'TestScenarios' in content:
            print(f"✅ Response contains TestScenarios")
            
            # Try to extract JSON from the content
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                try:
                    parsed_json = json.loads(json_match.group(1))
                    test_scenarios = parsed_json.get('TestScenarios', [])
                    print(f"✅ Found {len(test_scenarios)} test scenarios")
                    
                    if test_scenarios:
                        first_scenario = test_scenarios[0]
                        print(f"\nFirst Scenario:")
                        print(f"  ScenarioID: {first_scenario.get('ScenarioID')}")
                        print(f"  Title: {first_scenario.get('Title')}")
                        print(f"  Category: {first_scenario.get('Category')}")
                        print(f"  Description: {first_scenario.get('Description')[:100]}...")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")
            else:
                print(f"❌ No JSON block found in content")
                print(f"Content preview: {content[:200]}...")
        else:
            print(f"❌ Response does not contain TestScenarios")
            print(f"Content preview: {content[:200]}...")
        
    else:
        print(f"❌ Test failed!")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")
