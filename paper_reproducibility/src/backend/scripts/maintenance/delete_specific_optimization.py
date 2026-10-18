"""
Check and delete test_case_optimization from the specific record
"""
import asyncio
from core.database import get_database
from bson import ObjectId

async def delete_optimization_from_record():
    """Delete test_case_optimization from the specified record"""
    db = await get_database()
    collection = db["session_history"]
    
    # Get the specific record
    record_id = ObjectId('6963e9ae3610ae32a8974d69')
    record = await collection.find_one({"_id": record_id})
    
    if not record:
        print("❌ Record not found!")
        return
    
    print("=" * 80)
    print("RECORD DETAILS")
    print("=" * 80)
    print(f"\nRecord ID: {record.get('_id')}")
    print(f"Session ID: {record.get('session_id')}")
    print(f"Created At: {record.get('created_at')}")
    print(f"Updated At: {record.get('updated_at')}")
    
    processes = record.get("processes", {})
    process_list = list(processes.keys())
    
    print(f"\nProcesses ({len(process_list)} total):")
    for idx, process_name in enumerate(process_list, 1):
        marker = " <- WILL BE DELETED" if process_name == "test_case_optimization" else ""
        print(f"  {idx}. {process_name}{marker}")
    
    # Check conditions
    print("\n" + "=" * 80)
    print("CONDITION CHECK:")
    print("=" * 80)
    
    if len(process_list) == 3:
        print(f"  ✅ Total processes: 3")
    else:
        print(f"  ❌ Total processes: {len(process_list)} (expected 3)")
    
    if len(process_list) > 0 and process_list[-1] == "test_case_optimization":
        print(f"  ✅ Last process: test_case_optimization")
    else:
        print(f"  ❌ Last process: {process_list[-1] if process_list else 'None'} (expected test_case_optimization)")
    
    # Delete if conditions are met
    if len(process_list) == 3 and process_list[-1] == "test_case_optimization":
        print("\n" + "=" * 80)
        print("DELETING test_case_optimization...")
        print("=" * 80)
        
        result = await collection.update_one(
            {"_id": record_id},
            {"$unset": {"processes.test_case_optimization": ""}}
        )
        
        if result.modified_count > 0:
            print("\n✅ Successfully deleted 'test_case_optimization'")
            
            # Verify deletion
            updated_record = await collection.find_one({"_id": record_id})
            remaining_processes = list(updated_record.get("processes", {}).keys())
            
            print("\nRemaining processes after deletion:")
            for idx, process_name in enumerate(remaining_processes, 1):
                print(f"  {idx}. {process_name}")
            
            print("\n" + "=" * 80)
            print("OPERATION COMPLETED SUCCESSFULLY")
            print("=" * 80)
        else:
            print("\n❌ Failed to delete - no changes made")
    else:
        print("\n" + "=" * 80)
        print("❌ CONDITIONS NOT MET - No deletion performed")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(delete_optimization_from_record())
