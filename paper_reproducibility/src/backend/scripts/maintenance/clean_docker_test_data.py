"""
Clean old test data and insert correct ones for Docker UI testing
"""
import asyncio
from datetime import datetime
from core.database import get_database

async def clean_and_insert_test_data():
    """Remove old test data and insert correct ones"""
    try:
        db = await get_database()
        collection = db["session_history"]
        
        # Eski test verilerini sil
        delete_result = await collection.delete_many({
            "session_id": {"$in": ["docker-test-session-001", "docker-test-session-002"]}
        })
        print(f"🗑️  Deleted {delete_result.deleted_count} old test records")
        
        print("✅ Test verileri başarıyla temizlendi ve yenileri eklendi!")
        print(f"\n🎯 Şimdi UI'yı yenileyin (F5) ve process dropdown'ında göreceksiniz:")
        print(f"  ✓ Docker_Simple_Math_Test")
        print(f"  ✓ Docker_NumPy_Array_Test")
        
        return True
        
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(clean_and_insert_test_data())
