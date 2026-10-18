"""
Gemini2.5-Flash-Test-Scenarios-from-Reqs process'i için
unique test case sayısını kontrol et
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = "stlc_database"

def check_process_unique_test_cases():
    """Belirli bir process için unique test case sayısını kontrol et"""
    
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    process_title = "Gemini2.5-Flash-Test-Scenarios-from-Reqs"
    
    print(f"🔍 Process: {process_title}")
    print("=" * 80)
    
    # 1. Test Case Optimization koleksiyonunda kontrol
    print("\n1️⃣ TEST CASE OPTIMIZATION COLLECTION:")
    optimization_collection = db["test_case_optimizations"]
    
    optimization_result = optimization_collection.find_one(
        {"process_title": process_title}
    )
    
    if optimization_result:
        unique_cases = optimization_result.get("optimization_results", {}).get("unique_test_cases", [])
        print(f"   ✅ Found optimization record")
        print(f"   📊 Unique Test Cases: {len(unique_cases)}")
        
        # İlk 3 test case'i göster
        print(f"\n   📝 Sample Test Cases (first 3):")
        for i, tc in enumerate(unique_cases[:3], 1):
            tc_id = tc.get("TestCaseID", "N/A")
            title = tc.get("Title", "N/A")
            print(f"      {i}. {tc_id}: {title}")
        
        if len(unique_cases) > 3:
            print(f"      ... and {len(unique_cases) - 3} more")
    else:
        print(f"   ❌ No optimization record found")
    
    # 2. Session History'de kontrol
    print("\n2️⃣ SESSION HISTORY:")
    session_collection = db["session_history"]
    
    # Test Case Generation sonuçlarını ara
    pipeline = [
        {
            "$match": {
                "processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": process_title
            }
        },
        {
            "$project": {
                "session_id": 1,
                "test_case_results": "$processes.test_case_generation.output.data.test_case_results"
            }
        }
    ]
    
    sessions = list(session_collection.aggregate(pipeline))
    
    if sessions:
        print(f"   ✅ Found {len(sessions)} session(s) with test case generation")
        
        total_test_cases = 0
        for session in sessions:
            session_id = session.get("session_id", "Unknown")
            test_case_results = session.get("test_case_results", [])
            
            session_test_count = 0
            for result in test_case_results:
                test_cases = result.get("test_cases", [])
                session_test_count += len(test_cases)
            
            total_test_cases += session_test_count
            print(f"   📄 Session {session_id}: {session_test_count} test cases")
        
        print(f"\n   📊 Total Test Cases (before optimization): {total_test_cases}")
    else:
        print(f"   ❌ No sessions found")
    
    # 3. Test Code Generation sonuçlarını kontrol
    print("\n3️⃣ TEST CODE GENERATION RESULTS:")
    
    # Session history'de test code generation sonuçlarını ara
    pipeline = [
        {
            "$match": {
                "processes.test_code_generation.process_title": process_title
            }
        },
        {
            "$project": {
                "session_id": 1,
                "code_generation_process_name": "$processes.test_code_generation.code_generation_process_name",
                "generated_tests": "$processes.test_code_generation.output.generated_tests",
                "total_test_cases": "$processes.test_code_generation.output.total_test_cases",
                "generated_count": "$processes.test_code_generation.output.generated_count",
                "timestamp": "$processes.test_code_generation.timestamp"
            }
        },
        {
            "$sort": {"timestamp": -1}
        }
    ]
    
    code_gen_sessions = list(session_collection.aggregate(pipeline))
    
    if code_gen_sessions:
        print(f"   ✅ Found {len(code_gen_sessions)} test code generation session(s)")
        
        for i, session in enumerate(code_gen_sessions, 1):
            session_id = session.get("session_id", "Unknown")
            process_name = session.get("code_generation_process_name", "N/A")
            total = session.get("total_test_cases", 0)
            generated = session.get("generated_count", 0)
            timestamp = session.get("timestamp", "Unknown")
            
            print(f"\n   📄 Session {i}: {session_id}")
            print(f"      Process Name: {process_name}")
            print(f"      Total Test Cases: {total}")
            print(f"      Generated: {generated}")
            print(f"      Timestamp: {timestamp}")
            
            # Generated tests detayını göster
            generated_tests = session.get("generated_tests", [])
            if generated_tests:
                success_count = len([t for t in generated_tests if t.get("status") == "success"])
                error_count = len([t for t in generated_tests if t.get("status") == "error"])
                print(f"      ✅ Success: {success_count}")
                print(f"      ❌ Errors: {error_count}")
    else:
        print(f"   ❌ No test code generation results found")
    
    # 4. Sonuç
    print("\n" + "=" * 80)
    print("📌 SUMMARY:")
    
    if optimization_result:
        unique_count = len(optimization_result.get("optimization_results", {}).get("unique_test_cases", []))
        print(f"✅ Expected test codes to generate: {unique_count}")
        print(f"   (Based on unique test cases in optimization)")
    
    if code_gen_sessions:
        latest_session = code_gen_sessions[0]
        actual_count = latest_session.get("generated_count", 0)
        total_count = latest_session.get("total_test_cases", 0)
        print(f"📊 Actual test codes generated: {actual_count} / {total_count}")
        
        if optimization_result:
            unique_count = len(optimization_result.get("optimization_results", {}).get("unique_test_cases", []))
            if actual_count == unique_count:
                print(f"✅ CORRECT: Generated count matches unique test cases!")
            else:
                print(f"⚠️  MISMATCH: Expected {unique_count}, but generated {actual_count}")
    
    client.close()

if __name__ == "__main__":
    try:
        check_process_unique_test_cases()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
