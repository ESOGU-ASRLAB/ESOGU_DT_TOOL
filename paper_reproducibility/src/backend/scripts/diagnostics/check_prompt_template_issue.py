"""
Check test_reporting_prompt template in database
"""
import asyncio
from core.database import get_database
import json

async def check_prompt_template():
    """Check the prompt template structure"""
    db = await get_database()
    collection = db["test_reporting_prompt"]
    
    prompt_doc = await collection.find_one({"process_type": "test_reporting"})
    
    if not prompt_doc:
        print("❌ test_reporting prompt bulunamadı!")
        return
    
    print("=" * 80)
    print("TEST REPORTING PROMPT TEMPLATE")
    print("=" * 80)
    
    prompt_text = prompt_doc.get("prompt_text", "")
    
    print(f"\nPrompt ID: {prompt_doc.get('_id')}")
    print(f"Process Type: {prompt_doc.get('process_type')}")
    print(f"Prompt Text Length: {len(prompt_text)} characters")
    
    # Check for curly braces that might be causing issues
    print("\n" + "=" * 80)
    print("SEARCHING FOR PROBLEMATIC PATTERNS")
    print("=" * 80)
    
    # Find all {xxx} patterns
    import re
    placeholders = re.findall(r'\{[^}]+\}', prompt_text)
    
    print(f"\nFound {len(placeholders)} placeholders:")
    for placeholder in set(placeholders):
        count = placeholders.count(placeholder)
        print(f"  - {placeholder} (appears {count} times)")
    
    # Check for the specific error pattern
    if '\n  "reportType"' in prompt_text:
        print(f"\n⚠️ Found the problematic pattern: '\\n  \"reportType\"'")
        
        # Find context around this pattern
        idx = prompt_text.find('\n  "reportType"')
        context_start = max(0, idx - 100)
        context_end = min(len(prompt_text), idx + 100)
        
        print("\nContext around the pattern:")
        print("-" * 80)
        print(prompt_text[context_start:context_end])
        print("-" * 80)
    
    # Check for JSON-like structures that might need escaping
    print("\n" + "=" * 80)
    print("CHECKING FOR JSON STRUCTURES")
    print("=" * 80)
    
    # Look for potential JSON blocks
    json_like_patterns = re.findall(r'\{[^{]*"[^"]*"[^}]*\}', prompt_text[:5000])
    
    if json_like_patterns:
        print(f"\nFound {len(json_like_patterns)} JSON-like patterns in first 5000 chars")
        for i, pattern in enumerate(json_like_patterns[:5], 1):
            print(f"\n{i}. {pattern[:100]}...")
    
    # Show the first part of the prompt
    print("\n" + "=" * 80)
    print("FIRST 1000 CHARACTERS OF PROMPT")
    print("=" * 80)
    print(prompt_text[:1000])
    print("...")

if __name__ == "__main__":
    asyncio.run(check_prompt_template())
