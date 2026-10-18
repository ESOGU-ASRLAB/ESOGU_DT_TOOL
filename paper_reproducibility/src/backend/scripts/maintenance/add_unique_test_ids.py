"""
Add unique identifiers to generated tests
"""
import asyncio
from core.database import get_database
import hashlib

async def add_unique_ids():
    db = await get_database()
    
    print("=" * 80)
    print("Adding unique identifiers to test codes")
    print("=" * 80)
    
    # Get all sessions with test_code_generation
    sessions = await db.session_history.find({
        "processes.test_code_generation": {"$exists": True}
    }).to_list(length=None)
    
    print(f"\n📊 Found {len(sessions)} sessions with test code generation")
    
    updated_count = 0
    
    for session in sessions:
        session_id = session.get('session_id')
        test_code_gen = session.get('processes', {}).get('test_code_generation', {})
        generated_tests = test_code_gen.get('output', {}).get('generated_tests', [])
        
        if not generated_tests:
            continue
        
        # Check if tests already have unique_id
        has_unique_id = any('unique_id' in test for test in generated_tests)
        if has_unique_id:
            print(f"  ⏭️  Session {session_id}: Already has unique IDs")
            continue
        
        # Add unique_id to each test
        for idx, test in enumerate(generated_tests):
            # Create unique ID from test_case_id + title + index
            test_id = test.get('test_case_id', '')
            title = test.get('title', '')
            
            # Use hash of test_case_id + title + index for uniqueness
            unique_str = f"{test_id}_{title}_{idx}"
            unique_id = hashlib.md5(unique_str.encode()).hexdigest()[:16]
            
            test['unique_id'] = unique_id
        
        # Update the session
        await db.session_history.update_one(
            {"session_id": session_id},
            {"$set": {"processes.test_code_generation.output.generated_tests": generated_tests}}
        )
        
        updated_count += 1
        print(f"  ✅ Session {session_id}: Added unique IDs to {len(generated_tests)} tests")
    
    print(f"\n✅ Updated {updated_count} sessions")

if __name__ == "__main__":
    asyncio.run(add_unique_ids())
