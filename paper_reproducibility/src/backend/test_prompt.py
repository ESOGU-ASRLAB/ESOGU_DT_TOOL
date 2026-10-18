#!/usr/bin/env python3
"""
Test script for generate_prompt function from backend directory
"""
import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from stlc.test_scenario_generation import generate_prompt

async def test_generate_prompt():
    """Test the generate_prompt function with sample data"""
    
    # Sample test data
    test_input = {
        "testType": "Functional Testing",
        "testCategory": "System Testing", 
        "model": "llama3.2:3b",
        "documentContent": "This is a sample document content for testing. It contains requirements for a web application that manages user accounts and authentication.",
        "selectedScoringElements": [
            {"name": "Test Coverage"},
            {"name": "Risk Assessment"},
            {"name": "Boundary Value Analysis"}
        ],
        "selectedInstructionElements": [
            {"name": "Follow ISTQB Standards"},
            {"name": "Include Positive and Negative Tests"},
            {"name": "Document Prerequisites"}
        ]
    }
    
    print("Testing generate_prompt function...")
    print(f"Input data keys: {list(test_input.keys())}")
    print("\n" + "="*50 + "\n")
    
    try:
        # Call the function
        print("Calling generate_prompt...")
        result = await generate_prompt(test_input, max_retries=2)  # Reduce retries for faster testing
        
        print("Result received:")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            print(f"Generated prompt length: {len(result.get('final_prompt', ''))}")
            print("\nGenerated prompt preview:")
            print("-" * 50)
            prompt = result.get('final_prompt', '')
            print(prompt[:800] + "..." if len(prompt) > 800 else prompt)
            print("-" * 50)
            print("SUCCESS: Prompt generated successfully!")
        else:
            print(f"ERROR: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generate_prompt())
