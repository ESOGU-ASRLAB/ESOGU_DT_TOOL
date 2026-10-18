#!/usr/bin/env python3
import os
import sys
from pymongo import MongoClient
from bson import ObjectId
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # MongoDB bağlantısı
    client = MongoClient('mongodb://localhost:27017/')
    db = client['stlc_database']
    
    print("MongoDB'ye bağlandı.")
    print("=" * 50)
    
    # session_history koleksiyonunu kontrol et
    session_history = db['session_history']
    
    # Koleksiyondaki toplam kayıt sayısı
    total_count = session_history.count_documents({})
    print(f"session_history koleksiyonunda toplam {total_count} kayıt var.")
    print("=" * 50)
    
    if total_count > 0:
        # Son 10 kaydı al
        print("Son 10 kayıt:")
        records = list(session_history.find().sort('_id', -1).limit(10))
        
        for i, record in enumerate(records, 1):
            print(f"\n--- Kayıt {i} ---")
            print(f"ID: {record.get('_id')}")
            print(f"Session ID: {record.get('session_id', 'N/A')}")
            print(f"Operation: {record.get('operation', 'N/A')}")
            print(f"Timestamp: {record.get('timestamp', 'N/A')}")
            
            # Test case sayısını kontrol et
            test_cases = record.get('test_cases', [])
            if test_cases:
                print(f"Test Case Sayısı: {len(test_cases)}")
                print(f"İlk test case: {test_cases[0] if test_cases else 'N/A'}")
            
            # Metadata varsa göster
            metadata = record.get('metadata', {})
            if metadata:
                print(f"Metadata: {metadata}")
            
            # Eğer çok fazla veri varsa kısalt
            record_copy = record.copy()
            if 'test_cases' in record_copy and len(record_copy['test_cases']) > 2:
                record_copy['test_cases'] = f"[{len(record_copy['test_cases'])} test cases...]"
            
            print(f"Tam kayıt: {json.dumps(record_copy, default=str, indent=2)}")
    
    # Tüm koleksiyonları listele
    print("\n" + "=" * 50)
    print("Veritabanındaki tüm koleksiyonlar:")
    collections = db.list_collection_names()
    for collection in collections:
        count = db[collection].count_documents({})
        print(f"- {collection}: {count} kayıt")
    
except Exception as e:
    print(f"Hata: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        client.close()
    except:
        pass
