"""
Check and delete test_case_optimization from the last record if it's the third process
"""
import asyncio
from core.database import get_database
from datetime import datetime

async def check_and_delete_last_optimization():
    """Check the last record and delete test_case_optimization if it's the third process"""
    db = await get_database()
    collection = db["session_history"]
    
    # Get the last record (most recent timestamp)
    last_record = await collection.find_one(
        {},
        sort=[("timestamp", -1)]
    )
    
    if not last_record:
        print("No records found!")
        return
    
    print("=" * 80)
    print("LAST RECORD IN SESSION_HISTORY")
    print("=" * 80)
    print(f"\nSession ID: {last_record.get('session_id')}")
    print(f"Timestamp: {last_record.get('timestamp')}")
    print(f"Record ID: {last_record.get('_id')}")
    
    processes = last_record.get("processes", {})
    process_list = list(processes.keys())
    
    print(f"\nProcesses ({len(process_list)} total):")
    for idx, process_name in enumerate(process_list, 1):
        print(f"  {idx}. {process_name}")
    
    # Check if there are exactly 3 processes and the last one is test_case_optimization
    if len(process_list) == 3 and process_list[-1] == "test_case_optimization":
        print("\n" + "=" * 80)
        print("CONDITIONS MET:")
        print("  ✅ Total processes: 3")
        print("  ✅ Last process: test_case_optimization")
        print("=" * 80)
        
        # Ask for confirmation
        print("\nDeleting 'test_case_optimization' from this record...")
        
        # Delete the test_case_optimization field
        result = await collection.update_one(
            {"_id": last_record["_id"]},
            {"$unset": {"processes.test_case_optimization": ""}}
        )
        
        if result.modified_count > 0:
            print("✅ Successfully deleted 'test_case_optimization' from the last record")
            
            # Verify deletion
            updated_record = await collection.find_one({"_id": last_record["_id"]})
            remaining_processes = list(updated_record.get("processes", {}).keys())
            
            print("\nRemaining processes after deletion:")
            for idx, process_name in enumerate(remaining_processes, 1):
                print(f"  {idx}. {process_name}")
        else:
            print("❌ Failed to delete - no changes made")
    else:
        print("\n" + "=" * 80)
        print("CONDITIONS NOT MET:")
        if len(process_list) != 3:
            print(f"  ❌ Total processes: {len(process_list)} (expected 3)")
        else:
            print(f"  ✅ Total processes: 3")
        
        if len(process_list) > 0 and process_list[-1] != "test_case_optimization":
            print(f"  ❌ Last process: {process_list[-1]} (expected test_case_optimization)")
        elif len(process_list) > 0:
            print(f"  ✅ Last process: test_case_optimization")
        
        print("=" * 80)
        print("\nNo deletion performed.")

if __name__ == "__main__":
    asyncio.run(check_and_delete_last_optimization())
