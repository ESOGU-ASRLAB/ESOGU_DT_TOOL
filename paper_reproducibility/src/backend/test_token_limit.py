#!/usr/bin/env python3
"""
Test script for token counting and model selection in Test Scenario Generation
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.text_splitter import count_tokens
from utils.model_client import LLMClient

def test_token_counting():
    """Test token counting functionality"""
    print("=== Token Counting Test ===")
    
    # Test small text
    small_text = "This is a small test text with just a few words."
    small_tokens = count_tokens(small_text)
    print(f"Small text: {small_text}")
    print(f"Tokens: {small_tokens}")
    print()
    
    # Test medium text
    medium_text = " ".join(["This is a test sentence."] * 100)
    medium_tokens = count_tokens(medium_text)
    print(f"Medium text length: {len(medium_text)} characters")
    print(f"Medium text tokens: {medium_tokens}")
    print()
    
    # Test large text (simulate large file content)
    large_text = " ".join(["This is a test sentence with many words to simulate a large file."] * 10000)
    large_tokens = count_tokens(large_text)
    print(f"Large text length: {len(large_text)} characters")
    print(f"Large text tokens: {large_tokens}")
    print()
    
    # Test token limit
    TOKEN_LIMIT = 4000
    print(f"Token limit: {TOKEN_LIMIT}")
    print(f"Small text exceeds limit: {small_tokens > TOKEN_LIMIT}")
    print(f"Medium text exceeds limit: {medium_tokens > TOKEN_LIMIT}")
    print(f"Large text exceeds limit: {large_tokens > TOKEN_LIMIT}")
    print()

def test_model_selection():
    """Test model selection logic"""
    print("=== Model Selection Test ===")
    
    # Test model client
    client = LLMClient()
    
    # Test normal model
    normal_model = "qwen2.5:7b"
    actual_normal = client.get_model_identifier(normal_model)
    print(f"Normal model: {normal_model} -> {actual_normal}")
    
    # Test high-capacity model
    high_capacity_model = "qwen2.5-7b-instruct-1m"
    actual_high_capacity = client.get_model_identifier(high_capacity_model)
    print(f"High-capacity model: {high_capacity_model} -> {actual_high_capacity}")
    print()

def test_logic_simulation():
    """Simulate the logic from test_scenario_generation.py"""
    print("=== Logic Simulation Test ===")
    
    # Simulate different content sizes
    test_cases = [
        ("Small content", "Small test content" * 10),
        ("Medium content", "Medium test content with more words" * 1000),  
        ("Large content", "Large test content that should exceed the token limit" * 15000)
    ]
    
    TOKEN_LIMIT = 4000
    
    for name, content in test_cases:
        tokens = count_tokens(content)
        model_name = "qwen2.5:7b"  # Default model
        
        print(f"\n{name}:")
        print(f"  Content length: {len(content)} characters")
        print(f"  Token count: {tokens}")
        print(f"  Original model: {model_name}")
        
        # Apply the same logic as in test_scenario_generation.py
        if tokens > TOKEN_LIMIT:
            print(f"  ⚠️ Token count ({tokens}) exceeds limit ({TOKEN_LIMIT})")
            if model_name != "qwen2.5-7b-instruct-1m":
                print(f"  🔄 Switching model from {model_name} to qwen2.5-7b-instruct-1m")
                model_name = "qwen2.5-7b-instruct-1m"
            else:
                print(f"  ✅ Already using high-capacity model")
        else:
            print(f"  ✅ Token count is within limit, using selected model: {model_name}")
        
        print(f"  Final model: {model_name}")

if __name__ == "__main__":
    print("Testing Token Limit and Model Selection for Test Scenario Generation")
    print("=" * 70)
    
    try:
        test_token_counting()
        test_model_selection() 
        test_logic_simulation()
        
        print("\n" + "=" * 70)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
