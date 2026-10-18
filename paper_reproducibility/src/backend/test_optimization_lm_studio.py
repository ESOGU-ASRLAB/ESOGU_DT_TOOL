#!/usr/bin/env python3
"""
Test script to verify LM Studio integration in Test Case Optimization
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

async def test_llm_similarity():
    """Test the LLM similarity function with sample test cases"""
    print("=== Testing LM Studio Integration in Test Case Optimization ===")
    
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
    
    case3 = TestCase(
        ScenarioID="TC003",
        TestCaseID="TC003", 
        Title="User Logout Functionality",
        Description="Test user logout process",
        Objective="Verify that user can logout successfully"
    )
    
    print(f"Test Case 1: {case1.Title}")
    print(f"Test Case 2: {case2.Title}")
    print(f"Test Case 3: {case3.Title}")
    
    try:        # Test similarity between case1 and case2 (should be similar)
        print("\n--- Testing Similarity: Case 1 vs Case 2 (Expected: Similar) ---")
        result1 = await _query_llm_similarity(case1, case2)
        print(f"Result: {result1}")
        
        # Test similarity between case1 and case3 (should be different)
        print("\n--- Testing Similarity: Case 1 vs Case 3 (Expected: Different) ---")
        result2 = await _query_llm_similarity(case1, case3)
        print(f"Result: {result2}")
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_smart_selection():
    """Test the smart selection process"""
    print("\n=== Testing Smart Selection Process ===")
    
    # Create sample test cases with some duplicates
    test_cases = [
        TestCase(
            ScenarioID="TC001",
            TestCaseID="TC001",
            Title="User Login with Valid Credentials",
            Description="Test successful login with correct username and password",
            Objective="Verify that user can login successfully with valid credentials"
        ),
        TestCase(
            ScenarioID="TC002", 
            TestCaseID="TC002",
            Title="Valid User Authentication",
            Description="Test login functionality with valid user credentials",
            Objective="Ensure successful authentication with correct login details"
        ),
        TestCase(
            ScenarioID="TC003",
            TestCaseID="TC003", 
            Title="User Logout Functionality",
            Description="Test user logout process",
            Objective="Verify that user can logout successfully"
        )
    ]
    
    try:        # Create TestCaseList and run smart selection
        test_case_list = TestCaseList(test_cases=test_cases)
        result = await smart_select(test_case_list)
        
        print(f"Original test cases: {len(test_cases)}")
        print(f"Unique test cases after optimization: {len(result.test_cases)}")
        print(f"Duplicate test cases found: {len(result.duplicates)}")
        print(f"Comparison logs: {len(result.comparison_logs)}")
        
        # Print unique test cases
        print("\n--- Unique Test Cases ---")
        for i, case in enumerate(result.test_cases, 1):
            print(f"{i}. {case.Title}")
        
        # Print duplicates
        if result.duplicates:
            print("\n--- Duplicate Test Cases ---")
            for i, dup in enumerate(result.duplicates, 1):
                print(f"{i}. Duplicate: {dup['DuplicateCase']['Title']}")
                print(f"   Matched with: {dup['MatchedWith']['Title']}")
        
        return True
        
    except Exception as e:
        print(f"Error during smart selection testing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_llm_client_direct():
    """Test LLMClient directly"""
    print("\n=== Testing LLMClient Direct Connection ===")
    
    try:
        client = LLMClient(model_name="llama-3.2-3b-instruct")
        
        test_prompt = """
You are given two test cases. Respond with JSON format:

TestCase1: Login Test
TestCase2: Authentication Test

Return: {"is_same": true}
"""
        
        response = await client.generate_response(
            prompt=test_prompt,
            temperature=0.1,
            max_tokens=100
        )
        
        print(f"LM Studio Response: {response}")
        return True
        
    except Exception as e:
        print(f"Error testing LLMClient: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("Starting LM Studio Integration Tests for Test Case Optimization\n")
        
        # Test 1: LLMClient direct connection
        success1 = await test_llm_client_direct()
        
        if success1:
            # Test 2: LLM similarity function
            success2 = await test_llm_similarity()
            
            if success2:
                # Test 3: Smart selection process
                success3 = await test_smart_selection()
                
                if success3:
                    print("\n🎉 All tests passed! LM Studio integration is working correctly.")
                else:
                    print("\n❌ Smart selection test failed.")
            else:
                print("\n❌ LLM similarity test failed.")
        else:
            print("\n❌ LLMClient direct test failed.")
    
    asyncio.run(main())
