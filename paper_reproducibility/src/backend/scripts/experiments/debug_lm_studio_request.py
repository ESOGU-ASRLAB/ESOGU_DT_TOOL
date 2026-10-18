#!/usr/bin/env python3
"""
Debug script to test LM Studio request format
"""

import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_lm_studio_request():
    """Test different request formats to LM Studio"""
    
    # First, let's check what models are available
    print("=== Testing Available Models ===")
    try:
        models_response = requests.get("http://localhost:1234/v1/models")
        print(f"Models response status: {models_response.status_code}")
        if models_response.status_code == 200:
            models_data = models_response.json()
            print(f"Available models: {json.dumps(models_data, indent=2)}")
            
            # Extract model names
            available_models = []
            if 'data' in models_data:
                for model in models_data['data']:
                    available_models.append(model.get('id', 'unknown'))
            print(f"Model IDs: {available_models}")
        else:
            print(f"Failed to get models: {models_response.text}")
            return
    except Exception as e:
        print(f"Error getting models: {e}")
        return
    
    # Test different payload formats
    print("\n=== Testing Chat Completions ===")
    
    # Test with the first available model
    if available_models:
        model_to_test = available_models[0]
        print(f"Testing with model: {model_to_test}")
        
        # Test 1: Simple user message
        payload1 = {
            "model": model_to_test,
            "messages": [
                {"role": "user", "content": "Hello, this is a test message. Please respond with 'Test successful'."}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        print(f"\nTest 1 - Simple user message:")
        print(f"Payload: {json.dumps(payload1, indent=2)}")
        
        try:
            response1 = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json=payload1,
                timeout=30
            )
            print(f"Response status: {response1.status_code}")
            print(f"Response headers: {dict(response1.headers)}")
            if response1.status_code == 200:
                print(f"Response: {json.dumps(response1.json(), indent=2)}")
            else:
                print(f"Error response: {response1.text}")
        except Exception as e:
            print(f"Exception during request: {e}")
        
        # Test 2: System + user message (like in our app)
        payload2 = {
            "model": model_to_test,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that responds to test messages."},
                {"role": "user", "content": "Hello, this is a test message. Please respond with 'Test successful'."}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        print(f"\nTest 2 - System + user message:")
        print(f"Payload: {json.dumps(payload2, indent=2)}")
        
        try:
            response2 = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json=payload2,
                timeout=30
            )
            print(f"Response status: {response2.status_code}")
            if response2.status_code == 200:
                print(f"Response: {json.dumps(response2.json(), indent=2)}")
            else:
                print(f"Error response: {response2.text}")
        except Exception as e:
            print(f"Exception during request: {e}")
            
        # Test 3: Test with only system message (like our current code)
        payload3 = {
            "model": model_to_test,
            "messages": [
                {"role": "system", "content": "Hello, this is a test message. Please respond with 'Test successful'."}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        print(f"\nTest 3 - Only system message:")
        print(f"Payload: {json.dumps(payload3, indent=2)}")
        
        try:
            response3 = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json=payload3,
                timeout=30
            )
            print(f"Response status: {response3.status_code}")
            if response3.status_code == 200:
                print(f"Response: {json.dumps(response3.json(), indent=2)}")
            else:
                print(f"Error response: {response3.text}")
        except Exception as e:
            print(f"Exception during request: {e}")

if __name__ == "__main__":
    test_lm_studio_request()
