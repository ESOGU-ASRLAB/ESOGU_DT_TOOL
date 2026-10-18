"""
Simple LM Studio connection test
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.model_client import LLMClient
import asyncio
import requests

def test_lm_studio_direct():
    """Test LM Studio directly without async"""
    try:
        print("🚀 Testing LM Studio connection directly...")
        
        # Test direct API call
        url = "http://localhost:1234/v1/chat/completions"
        payload = {
            "model": "llama-3.2-1b-instruct",
            "messages": [{"role": "system", "content": "Hello! Please respond with 'LM Studio is working' if you can see this message."}],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        print(f"📤 Sending request to: {url}")
        print(f"📤 Payload: {payload}")
        
        response = requests.post(url, json=payload, timeout=30)
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"📥 Response: {content}")
            print("✅ LM Studio connection successful!")
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing LM Studio: {str(e)}")
        return False

async def test_lm_studio_client():
    """Test through LLMClient"""
    try:
        print("\n🚀 Testing through LLMClient...")
        
        # Create LLMClient instance
        client = LLMClient()
        print(f"✅ LLMClient created with model: {client.model_name}")
        
        # Test a simple prompt
        test_prompt = "Hello! Please respond with 'LM Studio is working' if you can see this message."
        print(f"📤 Sending test prompt: {test_prompt}")
        
        response = await client.generate_response(test_prompt, temperature=0.1, max_tokens=50)
        print(f"📥 Response: {response}")
        
        if response:
            print("✅ LLMClient test successful!")
            return True
        else:
            print("❌ No response received from LLMClient")
            return False
            
    except Exception as e:
        print(f"❌ Error testing LLMClient: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Testing LM Studio Connection ===")
    
    # Test 1: Direct API call
    direct_success = test_lm_studio_direct()
    
    # Test 2: Through LLMClient
    if direct_success:
        client_success = asyncio.run(test_lm_studio_client())
        if client_success:
            print("\n🎉 All tests passed! LM Studio is working correctly.")
        else:
            print("\n⚠️ Direct API works but LLMClient has issues.")
    else:
        print("\n❌ LM Studio direct connection failed. Please check if LM Studio is running.")
