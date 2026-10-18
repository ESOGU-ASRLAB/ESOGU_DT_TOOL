#!/usr/bin/env python3
"""
Test script to verify test scenario generation database recording
"""

import requests
import json
import time

def test_test_scenario_generation():
    """Test the test scenario generation with database recording"""
    
    print("🧪 Testing Test Scenario Generation Database Recording")
    print("=" * 60)
    
    # Test data for scenario generation
    test_data = {
        "model": "llama3.2:3b",
        "final_prompt": """Generate comprehensive test scenarios for a user login system.

## Requirements to Test:
- User authentication with username/password
- Valid and invalid login attempts
- Password validation
- Session management
- Error handling

## JSON OUTPUT STRUCTURE:
You MUST respond with a valid JSON object in this exact structure:

```json
{
    "TestScenarios": [
        {
            "ScenarioID": "TS_001",
            "Title": "Valid User Login",
            "Description": "Test successful login with valid credentials. Verify that users can authenticate with correct username and password combinations.",
            "Objective": "Validate successful user authentication",
            "Category": "Functional",
            "Comments": "Basic positive test case"
        }
    ]
}
```

Generate 5-8 test scenarios for the login system.""",
        "test_category": "Functional",
        "test_type": "Functional Testing",
        "session_id": f"test_session_{int(time.time())}"
    }
    
    print(f"📤 Sending test scenario generation request...")
    print(f"   Session ID: {test_data['session_id']}")
    print(f"   Test Type: {test_data['test_type']}")
    print(f"   Category: {test_data['test_category']}")
    
    try:
        # Make request to the test scenario generation endpoint
        response = requests.post(
            "http://localhost:8000/api/processes/test-scenario-generation/run",
            data=test_data,
            headers={"Accept": "application/json"},
            timeout=120  # 2 minutes timeout
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test scenario generation successful!")
            
            # Print summary
            if "test_scenarios" in result:
                scenarios = result["test_scenarios"].get("TestScenarios", [])
                print(f"   Generated scenarios: {len(scenarios)}")
                
                for i, scenario in enumerate(scenarios[:3], 1):  # Show first 3
                    print(f"   {i}. {scenario.get('Title', 'Unknown')}")
                    
                if len(scenarios) > 3:
                    print(f"   ... and {len(scenarios) - 3} more scenarios")
            
            # Print metadata
            if "metadata" in result:
                metadata = result["metadata"]
                print(f"   Model used: {metadata.get('model_used', 'Unknown')}")
                print(f"   Files processed: {metadata.get('files_processed', 0)}")
                print(f"   Session ID: {metadata.get('session_id', 'Unknown')}")
            
            return True, test_data['session_id']
            
        else:
            print(f"❌ Test scenario generation failed!")
            print(f"   Error: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        print("⏱️ Request timed out (this is normal for AI generation)")
        return False, None
    except Exception as e:
        print(f"💥 Error during request: {e}")
        return False, None

def check_database_recording(session_id):
    """Check if the test scenario generation was recorded in the database"""
    
    print(f"\n🔍 Checking Database Recording for Session: {session_id}")
    print("=" * 60)
    
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://localhost:27017')
        db = client['stlc_database']
        
        # Check session_history for our session
        session_doc = db['session_history'].find_one({"session_id": session_id})
        
        if session_doc:
            print("✅ Session found in session_history collection")
            
            if 'processes' in session_doc and 'test_scenario_generation' in session_doc['processes']:
                tsg_data = session_doc['processes']['test_scenario_generation']
                print("✅ test_scenario_generation process data found")
                print(f"   Model used: {tsg_data.get('used_model', 'Unknown')}")
                print(f"   Timestamp: {tsg_data.get('timestamp', 'Unknown')}")
                
                if 'output' in tsg_data:
                    output = tsg_data['output']
                    if 'test_scenarios' in output:
                        scenarios = output['test_scenarios'].get('TestScenarios', [])
                        print(f"   Scenarios recorded: {len(scenarios)}")
                    
                    if 'metadata' in output:
                        metadata = output['metadata']
                        print(f"   Total scenarios: {metadata.get('total_scenarios', 0)}")
                        print(f"   Test type: {metadata.get('test_type', 'Unknown')}")
                
                return True
            else:
                print("❌ test_scenario_generation process data NOT found")
                return False
        else:
            print("❌ Session NOT found in database")
            return False
            
    except Exception as e:
        print(f"💥 Error checking database: {e}")
        return False
    finally:
        client.close()

def main():
    """Main test function"""
    
    print("🚀 Starting Test Scenario Generation Database Recording Test")
    print("=" * 70)
    
    # Test the generation
    success, session_id = test_test_scenario_generation()
    
    if success and session_id:
        # Wait a moment for database write
        print("\n⏳ Waiting for database write...")
        time.sleep(2)
        
        # Check database recording
        db_recorded = check_database_recording(session_id)
        
        if db_recorded:
            print(f"\n🎉 SUCCESS: Test scenario generation AND database recording working!")
        else:
            print(f"\n⚠️ PARTIAL SUCCESS: Generation worked but database recording failed")
    else:
        print(f"\n❌ FAILED: Test scenario generation failed")
    
    print("\n" + "=" * 70)
    print("Test completed!")

if __name__ == "__main__":
    main()
