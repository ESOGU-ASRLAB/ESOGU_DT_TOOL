#!/usr/bin/env python3
"""
Simple test for LLMClient
"""
import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from utils.model_client import LLMClient

async def test_llm_client():
    """Test the LLMClient directly"""
    print("Testing LLMClient...")
    
    try:
        # Create client
        client = LLMClient(model_name="llama-3.2-3b-instruct")
        print(f"Client created with model: {client.model_name}")
        
        # Simple test prompt
        test_prompt = "Generate a simple test scenario for login functionality. Respond in plain text."
        
        print("Sending test prompt...")
        response = await client.generate_response(test_prompt, temperature=0.3, max_tokens=200)
        
        print("Response received:")
        print(f"Length: {len(response) if response else 0}")
        print(f"Content: {response}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_client())
