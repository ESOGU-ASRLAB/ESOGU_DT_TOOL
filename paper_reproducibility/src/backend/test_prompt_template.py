"""
Test if the current prompt template works with the fixed code
"""
import asyncio
from core.database import get_database

async def test_template():
    """Test the prompt template formatting"""
    db = await get_database()
    collection = db["test_reporting_prompt"]
    
    prompt_doc = await collection.find_one({"process_type": "test_reporting"})
    
    if not prompt_doc:
        print("❌ Prompt not found!")
        return
    
    prompt_text = prompt_doc.get("prompt_text", "")
    
    print("=" * 80)
    print("TESTING PROMPT TEMPLATE")
    print("=" * 80)
    
    print(f"\nTemplate length: {len(prompt_text)} chars")
    
    # Test with dummy data (matching what the code sends)
    test_params = {
        "analysis_depth": "detailed",
        "session_count": 1,
        "process_types": "test_scenario_generation, test_case_generation",
        "date_range": "2025-01-01 to 2025-01-14",
        "session_data": '{"test": "data"}'
    }
    
    print("\nTest parameters:")
    for key, value in test_params.items():
        print(f"  {key}: {str(value)[:50]}...")
    
    print("\n" + "=" * 80)
    print("ATTEMPTING FORMAT")
    print("=" * 80)
    
    try:
        result = prompt_text.format(**test_params)
        print("\n✅ SUCCESS! Template formatted without errors")
        print(f"Result length: {len(result)} chars")
        
        # Check if JSON examples are preserved
        if '"reportType"' in result:
            print("✅ JSON examples preserved")
        if '"standardsCompliance"' in result:
            print("✅ Standards compliance section preserved")
        
        # Show a snippet
        print("\n" + "=" * 80)
        print("FIRST 500 CHARS OF RESULT")
        print("=" * 80)
        print(result[:500])
        
    except KeyError as e:
        print(f"\n❌ FAILED: Missing placeholder: {e}")
        print("\nPlaceholders found in template:")
        import re
        placeholders = set(re.findall(r'\{([^}]+)\}', prompt_text))
        for p in sorted(placeholders):
            in_params = "✅" if p in test_params else "❌"
            print(f"  {in_params} {{{p}}}")
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_template())
