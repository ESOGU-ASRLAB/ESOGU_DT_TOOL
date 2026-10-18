"""
Fix the test_reporting_prompt template in database
Escape curly braces in JSON examples
"""
import asyncio
from core.database import get_database
import re

async def fix_prompt_template():
    """Fix the prompt template by escaping curly braces in JSON examples"""
    db = await get_database()
    collection = db["test_reporting_prompt"]
    
    prompt_doc = await collection.find_one({"process_type": "test_reporting"})
    
    if not prompt_doc:
        print("❌ test_reporting prompt bulunamadı!")
        return
    
    print("=" * 80)
    print("FIXING TEST REPORTING PROMPT TEMPLATE")
    print("=" * 80)
    
    original_prompt = prompt_doc.get("prompt_text", "")
    
    print(f"\nOriginal Prompt Length: {len(original_prompt)} characters")
    
    # Find all placeholders that should NOT be escaped
    # These are the actual variables we want to replace
    valid_placeholders = [
        '{analysis_depth}',
        '{session_count}',
        '{process_types}',
        '{date_range}',
        '{session_data}',
        '{intermediate_summaries}'
    ]
    
    # Step 1: First, temporarily replace valid placeholders with unique markers
    temp_markers = {}
    fixed_prompt = original_prompt
    
    for i, placeholder in enumerate(valid_placeholders):
        marker = f"___TEMP_MARKER_{i}___"
        temp_markers[marker] = placeholder
        fixed_prompt = fixed_prompt.replace(placeholder, marker)
    
    # Step 2: Escape all remaining curly braces (these are JSON examples)
    fixed_prompt = fixed_prompt.replace('{', '{{').replace('}', '}}')
    
    # Step 3: Restore valid placeholders
    for marker, placeholder in temp_markers.items():
        fixed_prompt = fixed_prompt.replace(marker, placeholder)
    
    print(f"Fixed Prompt Length: {len(fixed_prompt)} characters")
    
    # Count changes
    original_count = original_prompt.count('{')
    fixed_count = fixed_prompt.count('{')
    
    print(f"\nCurly braces count:")
    print(f"  Original: {original_count} '{{' characters")
    print(f"  Fixed: {fixed_count} '{{' characters")
    print(f"  Change: {fixed_count - original_count} additional characters (for escaping)")
    
    # Show some examples of what was fixed
    print("\n" + "=" * 80)
    print("EXAMPLE OF FIXES")
    print("=" * 80)
    
    # Find a JSON example
    json_example_start = fixed_prompt.find('```json')
    if json_example_start != -1:
        json_example_end = fixed_prompt.find('```', json_example_start + 7)
        if json_example_end != -1:
            example = fixed_prompt[json_example_start:json_example_end + 3]
            print("\nExample JSON block (first 500 chars):")
            print(example[:500])
    
    # Verify that our valid placeholders are still there
    print("\n" + "=" * 80)
    print("VERIFYING VALID PLACEHOLDERS")
    print("=" * 80)
    
    for placeholder in valid_placeholders:
        if placeholder in fixed_prompt:
            print(f"  ✅ {placeholder} - Found")
        else:
            print(f"  ❌ {placeholder} - NOT FOUND (ERROR!)")
    
    # Update the database
    print("\n" + "=" * 80)
    print("UPDATING DATABASE")
    print("=" * 80)
    
    result = await collection.update_one(
        {"process_type": "test_reporting"},
        {"$set": {"prompt_text": fixed_prompt}}
    )
    
    if result.modified_count > 0:
        print("\n✅ Prompt template başarıyla güncellendi!")
        print("\nDegişiklikler:")
        print(f"  - JSON örneklerindeki {{ }} karakterleri escape edildi")
        print(f"  - Geçerli placeholder'lar korundu: {', '.join(valid_placeholders)}")
    else:
        print("\n❌ Güncelleme başarısız!")
    
    print("\n" + "=" * 80)
    print("TEST: TRYING TO FORMAT WITH DUMMY DATA")
    print("=" * 80)
    
    # Test the fix
    try:
        test_result = fixed_prompt.format(
            analysis_depth="detailed",
            session_count=1,
            process_types="test_scenario_generation, test_case_generation",
            date_range="2025-01-01 to 2025-01-14",
            session_data='{"test": "data"}',
            intermediate_summaries="Test summary"
        )
        print("\n✅ Format test BAŞARILI! Template artık çalışıyor.")
        print(f"Formatted prompt length: {len(test_result)} characters")
    except KeyError as e:
        print(f"\n❌ Format test BAŞARISIZ: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_prompt_template())
