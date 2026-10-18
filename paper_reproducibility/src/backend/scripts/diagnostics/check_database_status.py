#!/usr/bin/env python3
"""
Test script to verify database recording functionality
"""

from pymongo import MongoClient
import json

def check_database_status():
    """Check the current state of the database"""
    client = MongoClient('mongodb://localhost:27017')
    db = client['stlc_database']
    
    print("🗄️ Database Status Check")
    print("=" * 50)
    
    # Check session_history
    session_count = db['session_history'].count_documents({})
    print(f"📊 session_history collection: {session_count} documents")
    
    # Check recent sessions
    print("\n📝 Recent sessions:")
    for doc in db['session_history'].find().sort('_id', -1).limit(5):
        session_id = doc.get('session_id', 'unknown')
        processes = list(doc.get('processes', {}).keys())
        print(f"  - {session_id}: {processes}")
    
    # Check test scenario specific collections
    collections = [
        'test_scenario_analytics',
        'test_scenario_quality', 
        'test_scenario_file_history'
    ]
    
    print(f"\n📈 Test Scenario Collections:")
    for collection_name in collections:
        count = db[collection_name].count_documents({})
        print(f"  - {collection_name}: {count} documents")
    
    # Check if any test_scenario_generation processes exist
    test_scenario_sessions = db['session_history'].count_documents({
        'processes.test_scenario_generation': {'$exists': True}
    })
    print(f"\n🎯 Test Scenario Generation sessions: {test_scenario_sessions}")
    
    client.close()

if __name__ == "__main__":
    check_database_status()
