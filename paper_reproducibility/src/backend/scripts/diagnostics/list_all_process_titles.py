"""
Database'deki tüm process title'ları listele
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = "stlc_database"

def list_all_process_titles():
    """Tüm process title'ları listele"""
    
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    print("🔍 LISTING ALL PROCESS TITLES IN DATABASE")
    print("=" * 80)
    
    # 1. Test Case Optimization koleksiyonu
    print("\n1️⃣ TEST CASE OPTIMIZATION COLLECTION:")
    optimization_collection = db["test_case_optimizations"]
    
    process_titles = optimization_collection.distinct("process_title")
    
    if process_titles:
        print(f"   Found {len(process_titles)} unique process titles:")
        for i, title in enumerate(sorted(process_titles), 1):
            # Her process için unique test case sayısını al
            result = optimization_collection.find_one({"process_title": title})
            if result:
                unique_cases = result.get("optimization_results", {}).get("unique_test_cases", [])
                print(f"   {i}. {title} ({len(unique_cases)} unique test cases)")
            else:
                print(f"   {i}. {title}")
    else:
        print("   ❌ No process titles found")
    
    # 2. Session History - Test Code Generation
    print("\n2️⃣ TEST CODE GENERATION PROCESSES:")
    session_collection = db["session_history"]
    
    # Test code generation'daki tüm process title'ları bul
    pipeline = [
        {
            "$match": {
                "processes.test_code_generation": {"$exists": True}
            }
        },
        {
            "$group": {
                "_id": "$processes.test_code_generation.process_title",
                "count": {"$sum": 1},
                "latest_session": {"$max": "$session_id"}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    code_gen_processes = list(session_collection.aggregate(pipeline))
    
    if code_gen_processes:
        print(f"   Found {len(code_gen_processes)} process titles with test code generation:")
        for i, proc in enumerate(code_gen_processes, 1):
            title = proc.get("_id", "Unknown")
            count = proc.get("count", 0)
            print(f"   {i}. {title} ({count} session(s))")
    else:
        print("   ❌ No test code generation processes found")
    
    # 3. Session History - Test Case Generation
    print("\n3️⃣ TEST CASE GENERATION PROCESSES:")
    
    # Test case generation'daki tüm process title'ları bul
    pipeline = [
        {
            "$match": {
                "processes.test_case_generation": {"$exists": True}
            }
        },
        {
            "$unwind": {
                "path": "$processes.test_case_generation.output.data.test_case_results",
                "preserveNullAndEmptyArrays": False
            }
        },
        {
            "$group": {
                "_id": "$processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    test_case_processes = list(session_collection.aggregate(pipeline))
    
    if test_case_processes:
        print(f"   Found {len(test_case_processes)} process titles with test case generation:")
        for i, proc in enumerate(test_case_processes, 1):
            title = proc.get("_id", "Unknown")
            count = proc.get("count", 0)
            if title and title != "Unknown":
                print(f"   {i}. {title} ({count} result(s))")
    else:
        print("   ❌ No test case generation processes found")
    
    # 4. "Gemini" kelimesini içeren process'leri ara
    print("\n4️⃣ PROCESSES CONTAINING 'Gemini':")
    
    all_titles = set()
    
    # Optimization'dan
    for title in process_titles:
        if "gemini" in title.lower():
            all_titles.add(title)
    
    # Code generation'dan
    for proc in code_gen_processes:
        title = proc.get("_id", "")
        if title and "gemini" in title.lower():
            all_titles.add(title)
    
    # Test case generation'dan
    for proc in test_case_processes:
        title = proc.get("_id", "")
        if title and "gemini" in title.lower():
            all_titles.add(title)
    
    if all_titles:
        print(f"   Found {len(all_titles)} process(es) containing 'Gemini':")
        for i, title in enumerate(sorted(all_titles), 1):
            print(f"   {i}. {title}")
    else:
        print("   ❌ No processes containing 'Gemini' found")
    
    client.close()

if __name__ == "__main__":
    try:
        list_all_process_titles()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
