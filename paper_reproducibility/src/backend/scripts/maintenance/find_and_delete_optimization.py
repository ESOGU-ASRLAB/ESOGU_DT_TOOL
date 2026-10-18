"""
Find and delete test_case_optimization from the last record that has exactly 3 processes
"""
import asyncio
from core.database import get_database

async def find_and_delete_optimization():
    """Find the last record with 3 processes and delete test_case_optimization if it's the third"""
    db = await get_database()
    collection = db["session_history"]
    
    # Find all records with exactly 3 processes, sorted by timestamp descending
    cursor = collection.find({}, sort=[("timestamp", -1)])
    
    async for record in cursor:
        processes = record.get("processes", {})
        process_list = list(processes.keys())
        
        # Check if this record has exactly 3 processes
        if len(process_list) == 3:
            print("=" * 80)
            print("FOUND RECORD WITH 3 PROCESSES")
            print("=" * 80)
            print(f"\nSession ID: {record.get('session_id')}")
            print(f"Timestamp: {record.get('timestamp')}")
            print(f"Record ID: {record.get('_id')}")
            
            print(f"\nProcesses (in order):")
            for idx, process_name in enumerate(process_list, 1):
                marker = " <- WILL BE DELETED" if idx == 3 and process_name == "test_case_optimization" else ""
                print(f"  {idx}. {process_name}{marker}")
            
            # Check if the last process is test_case_optimization
            if process_list[-1] == "test_case_optimization":
                print("\n" + "=" * 80)
                print("✅ Last process is 'test_case_optimization' - DELETING...")
                print("=" * 80)
                
                # Delete the test_case_optimization field
                result = await collection.update_one(
                    {"_id": record["_id"]},
                    {"$unset": {"processes.test_case_optimization": ""}}
                )
                
                if result.modified_count > 0:
                    print("\n✅ Successfully deleted 'test_case_optimization'")
                    
                    # Verify deletion
                    updated_record = await collection.find_one({"_id": record["_id"]})
                    remaining_processes = list(updated_record.get("processes", {}).keys())
                    
                    print("\nRemaining processes:")
                    for idx, process_name in enumerate(remaining_processes, 1):
                        print(f"  {idx}. {process_name}")
                    
                    print("\n" + "=" * 80)
                    print("OPERATION COMPLETED SUCCESSFULLY")
                    print("=" * 80)
                else:
                    print("\n❌ Failed to delete - no changes made")
                
                break  # Stop after first match
            else:
                print(f"\n❌ Last process is '{process_list[-1]}', not 'test_case_optimization'")
                print("Checking next record...")
                print()
                continue
    else:
        print("=" * 80)
        print("NO MATCHING RECORD FOUND")
        print("=" * 80)
        print("\nNo record found with exactly 3 processes where the last one is 'test_case_optimization'")

if __name__ == "__main__":
    asyncio.run(find_and_delete_optimization())
