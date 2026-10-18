#!/usr/bin/env python3
"""
Test script to check if new models are available in the API
"""

import requests
import json

def test_models_api():
    """Test the models API endpoint"""
    try:
        print("=== Testing Model API Endpoint ===")
        
        response = requests.get('http://localhost:8000/api/test-case-optimization/models')
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                models = data.get('data', [])
                print(f"✅ API Response successful. Found {len(models)} models.")
                
                # Filter local models
                local_models = [m for m in models if m.get('type') == 'local']
                api_models = [m for m in models if m.get('type') == 'api']
                
                print(f"\n📍 Local Models ({len(local_models)}):")
                for model in local_models:
                    print(f"  • {model['key']}: {model['name']}")
                
                print(f"\n🌐 API Models ({len(api_models)}):")
                for model in api_models:
                    provider = model.get('provider', 'Unknown')
                    print(f"  • {model['key']}: {model['name']} ({provider})")
                
                # Check for our new models
                new_models = ['google/gemma-3-12b', 'qwen/qwen3-14b', 'gemini-2.5-pro']
                print(f"\n🔍 Checking for new models:")
                
                model_keys = [m['key'] for m in models]
                for new_model in new_models:
                    if new_model in model_keys:
                        print(f"  ✅ {new_model}: Found")
                    else:
                        print(f"  ❌ {new_model}: Missing")
                
                return True
            else:
                print(f"❌ API returned error: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    test_models_api()
