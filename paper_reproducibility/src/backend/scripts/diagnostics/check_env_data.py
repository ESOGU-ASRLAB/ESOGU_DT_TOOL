#!/usr/bin/env python3
"""
Check Environment Setup data in MongoDB
"""

from core.database import get_db

def check_environment_data():
    try:
        db = get_db()
        collection = db['session_history']
        
        # Environment setup kayıtlarını say
        count = collection.count_documents({'processes.environment_setup': {'$exists': True}})
        print(f"📊 Total records with environment_setup: {count}")
        
        # İlk 3 kaydı al
        cursor = collection.find(
            {'processes.environment_setup': {'$exists': True}}, 
            {
                'session_id': 1, 
                'processes.environment_setup.environment_name': 1, 
                'processes.environment_setup.timestamp': 1
            }
        ).limit(3)
        
        print("\n🔍 Sample records:")
        for i, doc in enumerate(cursor, 1):
            env_setup = doc.get('processes', {}).get('environment_setup', {})
            env_name = env_setup.get('environment_name', 'N/A')
            timestamp = env_setup.get('timestamp', 'N/A')
            session_id = doc.get('session_id', str(doc.get('_id', 'N/A')))
            print(f"  {i}. Session: {session_id}")
            print(f"     Environment: {env_name}")
            print(f"     Timestamp: {timestamp}")
            print()
        
        print("✅ Data check completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_environment_data()