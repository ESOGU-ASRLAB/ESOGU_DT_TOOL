"""
Test Code Generation'ın veri yapısını kontrol et
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = "stlc_database"

def check_data_structure():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    print("=" * 80)
    print("🔍 CURRENT DATA STRUCTURE ANALYSIS")
    print("=" * 80)
    
    # 1. test_case_optimizations koleksiyonunu kontrol et
    print("\n1️⃣ test_case_optimizations COLLECTION:")
    opt_coll = db["test_case_optimizations"]
    opt_count = opt_coll.count_documents({})
    print(f"   Total documents: {opt_count}")
    
    if opt_count > 0:
        sample = opt_coll.find_one()
        print(f"\n   Sample Document Structure:")
        print(f"   - _id: {sample.get('_id')}")
        print(f"   - process_title: {sample.get('process_title', 'N/A')}")
        print(f"   - Keys: {list(sample.keys())}")
        
        if 'optimization_results' in sample:
            opt_results = sample['optimization_results']
            if isinstance(opt_results, dict):
                print(f"   - optimization_results keys: {list(opt_results.keys())}")
                if 'unique_test_cases' in opt_results:
                    unique_count = len(opt_results['unique_test_cases'])
                    print(f"   - unique_test_cases count: {unique_count}")
    
    # 2. session_history'de test_case_optimization'ı kontrol et
    print("\n2️⃣ session_history->processes->test_case_optimization:")
    session_coll = db["session_history"]
    
    pipeline = [
        {
            "$match": {
                "processes.test_case_optimization": {"$exists": True}
            }
        },
        {
            "$project": {
                "session_id": 1,
                "process_name": "$processes.test_case_optimization.process_name",  # Doğru path
                "unique_test_cases_count": {
                    "$size": {
                        "$ifNull": ["$processes.test_case_optimization.output.unique_test_cases", []]
                    }
                },
                "timestamp": "$processes.test_case_optimization.timestamp"
            }
        },
        {
            "$limit": 5
        }
    ]
    
    sessions = list(session_coll.aggregate(pipeline))
    print(f"   Found {len(sessions)} session(s) with test_case_optimization")
    
    if sessions:
        for sess in sessions:
            print(f"   - session_id: {sess.get('session_id', 'N/A')}")
            print(f"      process_name: {sess.get('process_name', 'N/A')}")
            print(f"      unique_test_cases_count: {sess.get('unique_test_cases_count', 0)}")
            print(f"      timestamp: {sess.get('timestamp', 'N/A')}")
    
    # 3. Karşılaştırma
    print("\n" + "=" * 80)
    print("📊 COMPARISON:")
    print("=" * 80)
    
    print("\n✅ CURRENT STRUCTURE (How it works NOW):")
    print("   Process Titles FROM:")
    print("      stlc_database->test_case_optimizations->process_title (distinct)")
    print("\n   Unique Test Cases FROM:")
    print("      stlc_database->test_case_optimizations->optimization_results->unique_test_cases")
    
    print("\n🤔 PROPOSED STRUCTURE (User's suggestion):")
    print("   Process Names FROM:")
    print("      stlc_database->session_history->processes->test_case_optimization->process_name")
    print("\n   Unique Test Cases FROM:")
    print("      stlc_database->session_history->processes->test_case_optimization->output->unique_test_cases")
    
    print("\n💡 ANALYSIS:")
    
    # test_case_optimizations'da veri var mı?
    has_opt_collection = opt_count > 0
    # session_history'de test_case_optimization var mı?
    has_session_tco = len(sessions) > 0
    
    if has_opt_collection and not has_session_tco:
        print("   ⚠️  Data is ONLY in test_case_optimizations collection")
        print("   ⚠️  session_history does NOT have test_case_optimization data")
        print("   ➡️  Current structure is being used")
    elif not has_opt_collection and has_session_tco:
        print("   ⚠️  Data is ONLY in session_history->test_case_optimization")
        print("   ⚠️  test_case_optimizations collection is empty")
        print("   ➡️  Proposed structure is available")
    elif has_opt_collection and has_session_tco:
        print("   ✅ Data exists in BOTH locations")
        print("   ➡️  Can migrate to session_history structure")
    else:
        print("   ❌ No data found in either location")
    
    client.close()

if __name__ == "__main__":
    try:
        check_data_structure()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
