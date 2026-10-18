"""
More comprehensive fix for the test_reporting_prompt template
"""
import asyncio
from core.database import get_database
import re

async def comprehensive_fix():
    """Comprehensive fix for all JSON examples in the prompt"""
    db = await get_database()
    collection = db["test_reporting_prompt"]
    
    prompt_doc = await collection.find_one({"process_type": "test_reporting"})
    
    if not prompt_doc:
        print("❌ test_reporting prompt bulunamadı!")
        return
    
    print("=" * 80)
    print("COMPREHENSIVE FIX FOR PROMPT TEMPLATE")
    print("=" * 80)
    
    original_prompt = prompt_doc.get("prompt_text", "")
    
    # Valid placeholders that should NOT be escaped
    valid_placeholders = [
        '{analysis_depth}',
        '{session_count}',
        '{process_types}',
        '{date_range}',
        '{session_data}',
        '{intermediate_summaries}'
    ]
    
    print(f"\nOriginal length: {len(original_prompt)} chars")
    left_brace_count = original_prompt.count('{')
    print(f"Original '{{' count: {left_brace_count}")
    
    # Create a more robust fix
    fixed_prompt = original_prompt
    
    # Step 1: Replace valid placeholders with unique markers
    temp_markers = {}
    for i, placeholder in enumerate(valid_placeholders):
        marker = f"___PLACEHOLDER_{i}___"
        temp_markers[marker] = placeholder
        fixed_prompt = fixed_prompt.replace(placeholder, marker)
        print(f"  Replaced {placeholder} with {marker}")
    
    # Step 2: Find all remaining single { and } and double them
    # But be careful not to double already doubled ones
    result = []
    i = 0
    while i < len(fixed_prompt):
        char = fixed_prompt[i]
        
        if char == '{':
            # Check if it's already doubled
            if i + 1 < len(fixed_prompt) and fixed_prompt[i + 1] == '{':
                # Already doubled, keep as is
                result.append('{{')
                i += 2
            else:
                # Single brace, double it
                result.append('{{')
                i += 1
        elif char == '}':
            # Check if it's already doubled
            if i + 1 < len(fixed_prompt) and fixed_prompt[i + 1] == '}':
                # Already doubled, keep as is
                result.append('}}')
                i += 2
            else:
                # Single brace, double it
                result.append('}}')
                i += 1
        else:
            result.append(char)
            i += 1
    
    fixed_prompt = ''.join(result)
    
    # Step 3: Restore valid placeholders
    for marker, placeholder in temp_markers.items():
        fixed_prompt = fixed_prompt.replace(marker, placeholder)
        print(f"  Restored {marker} back to {placeholder}")
    
    fixed_length = len(fixed_prompt)
    fixed_left_brace_count = fixed_prompt.count('{')
    print(f"\nFixed length: {fixed_length} chars")
    print(f"Fixed '{{' count: {fixed_left_brace_count}")
    
    # Verify placeholders
    print("\n" + "=" * 80)
    print("VERIFYING VALID PLACEHOLDERS")
    print("=" * 80)
    
    all_good = True
    for placeholder in valid_placeholders:
        count = fixed_prompt.count(placeholder)
        if count > 0:
            print(f"  ✅ {placeholder} - Found ({count} times)")
        else:
            print(f"  ❌ {placeholder} - NOT FOUND!")
            all_good = False
    
    if not all_good:
        print("\n⚠️ WARNING: Some placeholders are missing!")
        return
    
    # Test the fix
    print("\n" + "=" * 80)
    print("TESTING FORMAT OPERATION")
    print("=" * 80)
    
    try:
        test_result = fixed_prompt.format(
            analysis_depth="detailed",
            session_count=1,
            process_types="test_scenario_generation, test_case_generation",
            date_range="2025-01-01 to 2025-01-14",
            session_data='{"test": "data"}',
            intermediate_summaries="Test summary"
        )
        print("\n✅ Format test SUCCESSFUL!")
        print(f"Result length: {len(test_result)} chars")
        
        # Check that JSON examples are still intact
        if '"reportType"' in test_result:
            print("✅ JSON examples preserved correctly")
        
    except KeyError as e:
        print(f"\n❌ Format test FAILED: KeyError: {e}")
        return
    except Exception as e:
        print(f"\n❌ Format test FAILED: {type(e).__name__}: {e}")
        return
    
    # Update database
    print("\n" + "=" * 80)
    print("UPDATING DATABASE")
    print("=" * 80)
    
    result = await collection.update_one(
        {"process_type": "test_reporting"},
        {"$set": {"prompt_text": fixed_prompt}}
    )
    
    if result.modified_count > 0:
        print("\n✅ Database updated successfully!")
    else:
        print("\n⚠️ No changes made to database (already up to date)")
    
    print("\n" + "=" * 80)
    print("FIX COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(comprehensive_fix())
