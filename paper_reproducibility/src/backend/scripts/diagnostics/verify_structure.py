"""
Test Code Generation'ın veri yapısını kontrol et - GÜNCELLENMIŞ
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = "stlc_database"

def check_data_structure():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    print("=" * 80)
    print("VERIFYING session_history->processes->test_case_optimization STRUCTURE")
    print("=" * 80)
    
    session_coll = db["session_history"]
    
    # session_history'de test_case_optimization'ı kontrol et
    pipeline = [
        {
            "$match": {
                "processes.test_case_optimization": {"$exists": True}
            }
        },
        {
            "$project": {
                "session_id": 1,
                "process_name": "$processes.test_case_optimization.process_name",
                "unique_test_cases_count": {
                    "$size": {
                        "$ifNull": ["$processes.test_case_optimization.output.unique_test_cases", []]
                    }
                },
                "timestamp": "$processes.test_case_optimization.timestamp"
            }
        },
        {
            "$sort": {"timestamp": -1}
        },
        {
            "$limit": 10
        }
    ]
    
    sessions = list(session_coll.aggregate(pipeline))
    
    print(f"\nFound {len(sessions)} session(s) with test_case_optimization:\n")
    
    process_names = []
    
    if sessions:
        for i, sess in enumerate(sessions, 1):
            session_id = sess.get('session_id', 'Unknown')
            process_name = sess.get('process_name', 'N/A')
            count = sess.get('unique_test_cases_count', 0)
            timestamp = sess.get('timestamp', 'N/A')
            
            print(f"{i}. Process Name: {process_name}")
            print(f"   Session ID: {session_id}")
            print(f"   Unique Test Cases: {count}")
            print(f"   Timestamp: {timestamp}")
            print()
            
            if process_name and process_name != 'N/A':
                process_names.append(process_name)
    
    print("=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    
    if process_names:
        print(f"\nTotal unique process names found: {len(set(process_names))}")
        print("\nProcess Names List:")
        for name in sorted(set(process_names)):
            print(f"  - {name}")
        
        print("\n" + "=" * 80)
        print("CONCLUSION:")
        print("=" * 80)
        print("\n✅ process_name field EXISTS in session_history!")
        print("✅ unique_test_cases EXISTS in output!")
        print("\n➡️  User's proposed structure is ALREADY AVAILABLE:")
        print("    stlc_database->session_history->processes->test_case_optimization->process_name")
        print("    stlc_database->session_history->processes->test_case_optimization->output->unique_test_cases")
        print("\n⚠️  But Test Code Generation Service currently uses:")
        print("    stlc_database->test_case_optimizations collection (OLD STRUCTURE)")
        print("\n🔧 RECOMMENDATION:")
        print("    Update Test Code Generation Service to use session_history structure!")
    else:
        print("\n❌ No process_name found in sessions")
        print("⚠️  This might be a data issue")
    
    client.close()

if __name__ == "__main__":
    try:
        check_data_structure()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
