"""
Delete test_case_optimization from a specific session by session_id
"""
import asyncio
from core.database import get_database

async def delete_optimization_from_session():
    """Delete test_case_optimization from the specified session"""
    db = await get_database()
    collection = db["session_history"]
    
    # Get the specific record by session_id
    session_id = "07bd8670-06de-4587-8e23-6c3f16dfea56"
    record = await collection.find_one({"session_id": session_id})
    
    if not record:
        print("❌ Session bulunamadı!")
        return
    
    print("=" * 80)
    print("SESSION DETAYLARI")
    print("=" * 80)
    print(f"\nRecord ID: {record.get('_id')}")
    print(f"Session ID: {record.get('session_id')}")
    print(f"Created At: {record.get('created_at')}")
    print(f"Updated At: {record.get('updated_at')}")
    
    processes = record.get("processes", {})
    process_list = list(processes.keys())
    
    print(f"\nProcesses ({len(process_list)} adet):")
    for idx, process_name in enumerate(process_list, 1):
        marker = " <- SİLİNECEK" if process_name == "test_case_optimization" else ""
        print(f"  {idx}. {process_name}{marker}")
    
    # Check if test_case_optimization exists
    print("\n" + "=" * 80)
    print("KONTROL:")
    print("=" * 80)
    
    if "test_case_optimization" in processes:
        print(f"  ✅ test_case_optimization bulundu")
        
        print("\n" + "=" * 80)
        print("test_case_optimization SİLİNİYOR...")
        print("=" * 80)
        
        result = await collection.update_one(
            {"session_id": session_id},
            {"$unset": {"processes.test_case_optimization": ""}}
        )
        
        if result.modified_count > 0:
            print("\n✅ 'test_case_optimization' başarıyla silindi!")
            
            # Verify deletion
            updated_record = await collection.find_one({"session_id": session_id})
            remaining_processes = list(updated_record.get("processes", {}).keys())
            
            print("\nSilme işleminden sonra kalan processler:")
            for idx, process_name in enumerate(remaining_processes, 1):
                print(f"  {idx}. {process_name}")
            
            print("\n" + "=" * 80)
            print("İŞLEM BAŞARIYLA TAMAMLANDI")
            print("=" * 80)
        else:
            print("\n❌ Silme başarısız - hiçbir değişiklik yapılmadı")
    else:
        print(f"  ❌ test_case_optimization bulunamadı")
        print("\n" + "=" * 80)
        print("❌ test_case_optimization BULUNAMADI - Silme işlemi yapılmadı")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(delete_optimization_from_session())
