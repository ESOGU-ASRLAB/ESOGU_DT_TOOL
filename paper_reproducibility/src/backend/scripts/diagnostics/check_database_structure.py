"""
Database koleksiyonlarını ve içeriklerini kontrol et
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = "stlc_database"

def check_database():
    """Database koleksiyonlarını kontrol et"""
    
    client = MongoClient(MONGO_URI)
    
    print("🔍 DATABASE INSPECTION")
    print("=" * 80)
    
    # Tüm database'leri listele
    print("\n📚 Available Databases:")
    dbs = client.list_database_names()
    for db_name in dbs:
        db = client[db_name]
        collections = db.list_collection_names()
        print(f"   - {db_name} ({len(collections)} collections)")
        if "stlc" in db_name.lower():
            print(f"     Collections: {', '.join(collections)}")
    
    # STLC Manager database'ini kontrol et
    print(f"\n📂 Database: {DATABASE_NAME}")
    db = client[DATABASE_NAME]
    collections = db.list_collection_names()
    
    if collections:
        print(f"   Found {len(collections)} collection(s):")
        for coll_name in collections:
            coll = db[coll_name]
            count = coll.count_documents({})
            print(f"   - {coll_name}: {count} document(s)")
            
            # İlk dokümanı göster
            if count > 0:
                sample = coll.find_one()
                if sample:
                    print(f"     Keys: {', '.join(list(sample.keys())[:10])}")
    else:
        print("   ❌ No collections found")
    
    # Session history detaylı kontrol
    print("\n📋 SESSION HISTORY DETAILS:")
    session_coll = db["session_history"]
    
    count = session_coll.count_documents({})
    print(f"   Total documents: {count}")
    
    if count > 0:
        # İlk 3 session'ı göster
        sessions = list(session_coll.find().limit(3))
        for i, sess in enumerate(sessions, 1):
            session_id = sess.get("session_id", "Unknown")
            processes = sess.get("processes", {})
            
            print(f"\n   Session {i}: {session_id}")
            print(f"      Processes: {', '.join(processes.keys())}")
            
            # Test code generation varsa detay göster
            if "test_code_generation" in processes:
                tcg = processes["test_code_generation"]
                proc_title = tcg.get("process_title", "N/A")
                process_name = tcg.get("code_generation_process_name", "N/A")
                output = tcg.get("output", {})
                total = output.get("total_test_cases", 0)
                generated = output.get("generated_count", 0)
                
                print(f"      Test Code Generation:")
                print(f"         Process Title: {proc_title}")
                print(f"         Process Name: {process_name}")
                print(f"         Total: {total}, Generated: {generated}")
    
    client.close()

if __name__ == "__main__":
    try:
        check_database()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
