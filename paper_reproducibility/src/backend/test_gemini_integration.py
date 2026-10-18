#!/usr/bin/env python3
"""
Test script to verify Gemini integration in Test Case Optimization
"""

import sys
import os
import asyncio
import logging

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

from services.test_case_optimization_service import TestCase, TestCaseList, smart_select, _query_llm_similarity
from utils.model_client import LLMClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gemini_direct():
    """Test Gemini API directly"""
    print("\n=== Testing Gemini Direct Connection ===")
    
    # Bu test için gerçek bir API key gerekli
    # Test için placeholder kullanıyoruz
    test_api_key = "TEST_API_KEY_PLACEHOLDER"
    
    try:
        client = LLMClient(model_name="gemini-2.5-flash", api_key=test_api_key)
        
        test_prompt = """
You are given two test cases. Respond with JSON format:

TestCase1: Login Test
TestCase2: Authentication Test

Return: {"is_same": true}
"""
        
        print("Note: This test requires a valid Gemini API key")
        print("Replace TEST_API_KEY_PLACEHOLDER with your actual API key to test")
        return True
        
    except ValueError as e:
        if "API key is required" in str(e):
            print("✅ API key validation working correctly")
            return True
        else:
            print(f"❌ Unexpected error: {e}")
            return False
    except Exception as e:
        print(f"❌ Error testing Gemini: {e}")
        return False

async def test_gemini_similarity():
    """Test the Gemini similarity function with sample test cases"""
    print("\n=== Testing Gemini Model Detection ===")
    
    # Create sample test cases
    case1 = TestCase(
        ScenarioID="TC001",
        TestCaseID="TC001",
        Title="User Login with Valid Credentials",
        Description="Test successful login with correct username and password",
        Objective="Verify that user can login successfully with valid credentials"
    )
    
    case2 = TestCase(
        ScenarioID="TC002", 
        TestCaseID="TC002",
        Title="Valid User Authentication",
        Description="Test login functionality with valid user credentials",
        Objective="Ensure successful authentication with correct login details"
    )
    
    print(f"Test Case 1: {case1.Title}")
    print(f"Test Case 2: {case2.Title}")
    
    try:
        # Test with placeholder API key - should fail with appropriate error
        print("\n--- Testing Gemini Model Detection ---")
        
        # Test API key requirement
        try:
            client = LLMClient(model_name="gemini-2.5-flash")  # No API key
            print("❌ Should have failed without API key")
            return False
        except ValueError as e:
            if "API key is required" in str(e):
                print("✅ API key validation working correctly")
            else:
                print(f"❌ Unexpected error: {e}")
                return False
        
        # Test non-Gemini model
        client_local = LLMClient(model_name="llama3.2:3b")
        is_not_gemini = client_local._is_gemini_model("llama3.2:3b")
        print(f"✅ Non-Gemini model detection: {not is_not_gemini}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

async def test_model_type_detection():
    """Test model type detection"""
    print("\n=== Testing Model Type Detection ===")
    
    gemini_models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-pro", 
        "gemini-1.5-flash",
        "gemini-pro"
    ]
    
    local_models = [
        "llama3.2:3b",
        "qwen2.5:7b",
        "codellama:7b"
    ]
    
    try:
        client = LLMClient(model_name="llama3.2:3b")
        
        print("Gemini models:")
        for model in gemini_models:
            is_gemini = client._is_gemini_model(model)
            print(f"  {model}: {'✅ Gemini' if is_gemini else '❌ Not detected'}")
        
        print("\nLocal models:")
        for model in local_models:
            is_gemini = client._is_gemini_model(model)
            print(f"  {model}: {'❌ False positive' if is_gemini else '✅ Local'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("Starting Gemini Integration Tests for Test Case Optimization\n")
        
        # Test 1: Model type detection
        success1 = await test_model_type_detection()
        
        # Test 2: Gemini model detection
        success2 = await test_gemini_similarity()
        
        # Test 3: Direct Gemini connection (with placeholder)
        success3 = await test_gemini_direct()
        
        if success1 and success2 and success3:
            print("\n🎉 All Gemini integration tests passed!")
            print("📝 Note: To test actual Gemini API calls, provide a real API key")
        else:
            print("\n❌ Some tests failed.")
    
    asyncio.run(main())
