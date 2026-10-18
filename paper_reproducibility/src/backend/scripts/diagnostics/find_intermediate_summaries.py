"""
Find where intermediate_summaries placeholder is used
"""
import asyncio
from core.database import get_database

async def find_placeholder():
    """Find intermediate_summaries placeholder"""
    db = await get_database()
    collection = db["test_reporting_prompt"]
    
    prompt_doc = await collection.find_one({"process_type": "test_reporting"})
    
    if not prompt_doc:
        print("❌ Prompt not found!")
        return
    
    prompt_text = prompt_doc.get("prompt_text", "")
    
    # Search for the placeholder
    search_terms = [
        'intermediate_summaries',
        '{intermediate_summaries}',
        '{{intermediate_summaries}}',
        'intermediate_summaries}',
        '{intermediate_summaries'
    ]
    
    print("=" * 80)
    print("SEARCHING FOR INTERMEDIATE_SUMMARIES")
    print("=" * 80)
    
    for term in search_terms:
        count = prompt_text.count(term)
        if count > 0:
            print(f"\n✅ Found '{term}' - {count} times")
            
            # Find all positions
            idx = 0
            positions = []
            while True:
                idx = prompt_text.find(term, idx)
                if idx == -1:
                    break
                positions.append(idx)
                idx += 1
            
            # Show context around each occurrence
            for pos in positions:
                start = max(0, pos - 100)
                end = min(len(prompt_text), pos + len(term) + 100)
                context = prompt_text[start:end]
                
                print(f"\nPosition {pos}:")
                print("-" * 80)
                print(context)
                print("-" * 80)
        else:
            print(f"❌ Not found: '{term}'")
    
    # Also check if there's a pattern with newlines or spaces
    print("\n" + "=" * 80)
    print("CHECKING FOR VARIATIONS")
    print("=" * 80)
    
    # Split into lines and search
    lines = prompt_text.split('\n')
    for i, line in enumerate(lines, 1):
        if 'intermediate' in line.lower() or 'summaries' in line.lower():
            print(f"\nLine {i}: {line[:100]}")

if __name__ == "__main__":
    asyncio.run(find_placeholder())
