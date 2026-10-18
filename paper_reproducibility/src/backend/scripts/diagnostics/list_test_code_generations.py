"""
Tüm Test Code Generation sonuçlarını listele
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = "stlc_database"

def list_all_test_code_generations():
    """Tüm test code generation sonuçlarını listele"""
    
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    session_collection = db["session_history"]
    
    print("🔍 ALL TEST CODE GENERATION RESULTS")
    print("=" * 80)
    
    # Test code generation'ı olan tüm session'ları bul
    pipeline = [
        {
            "$match": {
                "processes.test_code_generation": {"$exists": True}
            }
        },
        {
            "$project": {
                "session_id": 1,
                "timestamp": "$processes.test_code_generation.timestamp",
                "process_title": "$processes.test_code_generation.process_title",
                "code_generation_process_name": "$processes.test_code_generation.code_generation_process_name",
                "total_test_cases": "$processes.test_code_generation.output.total_test_cases",
                "generated_count": "$processes.test_code_generation.output.generated_count",
                "failed_count": "$processes.test_code_generation.output.failed_count",
                "model_name": "$processes.test_code_generation.output.model_name"
            }
        },
        {
            "$sort": {"timestamp": -1}
        }
    ]
    
    results = list(session_collection.aggregate(pipeline))
    
    if results:
        print(f"✅ Found {len(results)} test code generation session(s)\n")
        
        for i, result in enumerate(results, 1):
            session_id = result.get("session_id", "Unknown")
            timestamp = result.get("timestamp", "Unknown")
            process_title = result.get("process_title", "N/A")
            process_name = result.get("code_generation_process_name", "N/A")
            total = result.get("total_test_cases", 0)
            generated = result.get("generated_count", 0)
            failed = result.get("failed_count", 0)
            model = result.get("model_name", "N/A")
            
            print(f"{'='*80}")
            print(f"📄 Session {i}: {session_id}")
            print(f"   🕐 Timestamp: {timestamp}")
            print(f"   📋 Process Title: {process_title}")
            print(f"   🏷️  Process Name: {process_name}")
            print(f"   🤖 Model: {model}")
            print(f"   📊 Test Cases: {total}")
            print(f"   ✅ Generated: {generated}")
            print(f"   ❌ Failed: {failed}")
            
            # Gemini içeren process'leri vurgula
            if "gemini" in process_title.lower() or "gemini" in process_name.lower():
                print(f"   ⭐ GEMINI PROCESS!")
    else:
        print("❌ No test code generation results found")
    
    # Özet istatistikler
    print(f"\n{'='*80}")
    print("📊 SUMMARY STATISTICS:")
    
    # Process Title'a göre grupla
    pipeline_summary = [
        {
            "$match": {
                "processes.test_code_generation": {"$exists": True}
            }
        },
        {
            "$group": {
                "_id": "$processes.test_code_generation.process_title",
                "total_sessions": {"$sum": 1},
                "avg_test_cases": {"$avg": "$processes.test_code_generation.output.total_test_cases"},
                "total_generated": {"$sum": "$processes.test_code_generation.output.generated_count"},
                "total_failed": {"$sum": "$processes.test_code_generation.output.failed_count"}
            }
        },
        {
            "$sort": {"total_sessions": -1}
        }
    ]
    
    summary = list(session_collection.aggregate(pipeline_summary))
    
    if summary:
        print(f"\n📈 By Process Title:")
        for proc in summary:
            title = proc.get("_id", "Unknown")
            sessions = proc.get("total_sessions", 0)
            avg_cases = proc.get("avg_test_cases", 0)
            total_gen = proc.get("total_generated", 0)
            total_fail = proc.get("total_failed", 0)
            
            print(f"\n   Process: {title}")
            print(f"      Sessions: {sessions}")
            print(f"      Avg Test Cases: {avg_cases:.1f}")
            print(f"      Total Generated: {total_gen}")
            print(f"      Total Failed: {total_fail}")
    
    client.close()

if __name__ == "__main__":
    try:
        list_all_test_code_generations()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
