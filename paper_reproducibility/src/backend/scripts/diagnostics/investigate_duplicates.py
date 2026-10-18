"""
Investigate duplicate test IDs in test_code_generation
"""
import asyncio
from core.database import get_database

async def investigate():
    db = await get_database()
    
    process_name = "ROS Test-27 Temmuz 2026"
    
    print("=" * 80)
    print(f"Investigating test structure for: {process_name}")
    print("=" * 80)
    
    # Get the most recent session
    pipeline = [
        {
            "$match": {
                "processes.test_code_generation": {"$exists": True},
                "processes.test_code_generation.process_name": process_name
            }
        },
        {
            "$project": {
                "session_id": 1,
                "timestamp": "$processes.test_code_generation.timestamp",
                "generated_tests": "$processes.test_code_generation.output.generated_tests",
                "process_name": "$processes.test_code_generation.process_name"
            }
        },
        {
            "$sort": {"timestamp": -1}
        },
        {
            "$limit": 1
        }
    ]
    
    results = await db.session_history.aggregate(pipeline).to_list(length=None)
    
    if not results:
        print("❌ No session found")
        return
    
    session = results[0]
    generated_tests = session.get("generated_tests", [])
    
    print(f"\n📊 Session: {session.get('session_id')}")
    print(f"   Total tests in session: {len(generated_tests)}")
    
    # Count test IDs
    test_id_counts = {}
    for test in generated_tests:
        test_id = test.get('test_case_id', 'NO_ID')
        if test_id not in test_id_counts:
            test_id_counts[test_id] = []
        test_id_counts[test_id].append({
            'title': test.get('title', ''),
            'code_len': len(test.get('code', '')),
            'status': test.get('status', '')
        })
    
    print("\n" + "=" * 80)
    print("TEST ID FREQUENCY:")
    print("=" * 80)
    for test_id, instances in sorted(test_id_counts.items()):
        print(f"\n{test_id}: {len(instances)} occurrences")
        for idx, instance in enumerate(instances, 1):
            print(f"  {idx}. {instance['title'][:60]}...")
            print(f"     Code: {instance['code_len']} chars, Status: {instance['status']}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION:")
    print("=" * 80)
    
    duplicates = {tid: instances for tid, instances in test_id_counts.items() if len(instances) > 1}
    
    if duplicates:
        print(f"❌ Found {len(duplicates)} test IDs with duplicates:")
        for tid, instances in duplicates.items():
            print(f"   {tid}: {len(instances)} times")
        print("\n💡 Solution: Use unique identifier (test_case_id + index) or filter by status")
    else:
        print("✅ No duplicates - all test IDs are unique")

if __name__ == "__main__":
    asyncio.run(investigate())
