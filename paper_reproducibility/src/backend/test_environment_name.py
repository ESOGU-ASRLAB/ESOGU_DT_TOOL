#!/usr/bin/env python3
"""
Test Environment Setup with Environment Name
Bu test environment_name field'ının düzgün kaydedilip kaydedilmediğini kontrol eder.
"""

import requests
import json

def test_environment_setup_with_name():
    """Environment Setup işlemi yapıp environment_name'in kaydedilip kaydedilmediğini test et"""
    print("🧪 Testing Environment Setup with environment_name...")
    
    # Test dosyası hazırla
    test_content = """
# Test Source Code
def test_function():
    return "Hello World"
"""
    
    # Form data hazırla
    files = {
        'files': ('test.py', test_content, 'text/plain')
    }
    
    data = {
        'types': 'Source Code',
        'environment_name': '26 Eylül Test 1',
        'model': 'llama3.2:3b',
        'session_id': 'test-session-26-eylul-2025'
    }
    
    try:
        print("📤 Sending Environment Setup request...")
        print(f"Environment Name: {data['environment_name']}")
        
        response = requests.post(
            'http://localhost:8000/api/processes/environment-setup/run',
            files=files,
            data=data,
            timeout=60
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Environment Setup başarılı!")
            print(f"Session ID: {result.get('session_id')}")
            
            # MongoDB'den kaydı kontrol et
            check_database_record(data['session_id'], data['environment_name'])
            
        else:
            print(f"❌ Environment Setup başarısız: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_database_record(session_id, expected_env_name):
    """Database'de kaydedilen environment_name'i kontrol et"""
    print(f"\n🔍 Checking database record for session: {session_id}")
    
    try:
        from core.database import get_db
        
        db = get_db()
        collection = db['session_history']
        
        # Session'ı bul
        record = collection.find_one({'session_id': session_id})
        
        if record:
            print("✅ Database record found!")
            
            # Environment setup process'ini kontrol et
            env_setup = record.get('processes', {}).get('environment_setup', {})
            
            if env_setup:
                actual_env_name = env_setup.get('environment_name', 'NOT_FOUND')
                timestamp = env_setup.get('timestamp', 'NOT_FOUND')
                
                print(f"📋 Environment Name: {actual_env_name}")
                print(f"📋 Expected: {expected_env_name}")
                print(f"📋 Timestamp: {timestamp}")
                
                if actual_env_name == expected_env_name:
                    print("✅ Environment name correctly saved!")
                else:
                    print("❌ Environment name mismatch!")
                    
            else:
                print("❌ Environment setup process not found in record")
        else:
            print("❌ Database record not found")
            
    except Exception as e:
        print(f"❌ Database check error: {e}")

if __name__ == "__main__":
    test_environment_setup_with_name()
    print("\n🎯 Test completed!")