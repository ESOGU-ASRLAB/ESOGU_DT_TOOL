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
    
    print("Test Case Sayısı Analizi")
    print("=" * 50)
    
    # Son session'ı al
    session_history = db['session_history']
    latest_session = session_history.find_one(sort=[('_id', -1)])
    
    if latest_session and 'processes' in latest_session:
        test_case_gen = latest_session['processes'].get('test_case_generation', {})
        
        if 'output' in test_case_gen:
            results = test_case_gen['output'].get('test_case_results', [])
            metadata = test_case_gen['output'].get('metadata', {})
            
            print(f"Session ID: {latest_session['session_id']}")
            print(f"Metadata'da toplam test case: {metadata.get('total_test_cases', 'N/A')}")
            print(f"İşlenen scenario sayısı: {metadata.get('scenarios_processed', 'N/A')}")
            print()
            
            total_actual_cases = 0
            for i, result in enumerate(results, 1):
                scenario_id = result.get('scenario_id')
                scenario_title = result.get('scenario_title')
                status = result.get('status')
                test_cases = result.get('test_cases', [])
                test_cases_count = result.get('test_cases_count', 0)
                
                print(f"Scenario {i}: {scenario_id}")
                print(f"  Başlık: {scenario_title}")
                print(f"  Durum: {status}")
                print(f"  Reported count: {test_cases_count}")
                print(f"  Actual test cases: {len(test_cases)}")
                
                if len(test_cases) > 0:
                    print(f"  İlk test case: {test_cases[0].get('TestCaseID', 'N/A')} - {test_cases[0].get('Title', 'N/A')}")
                    if len(test_cases) > 1:
                        print(f"  Son test case: {test_cases[-1].get('TestCaseID', 'N/A')} - {test_cases[-1].get('Title', 'N/A')}")
                
                total_actual_cases += len(test_cases)
                print()
            
            print(f"TOPLAM:")
            print(f"  Metadata'da belirtilen: {metadata.get('total_test_cases', 'N/A')}")
            print(f"  Gerçekte kaydedilen: {total_actual_cases}")
            print(f"  Fark: {metadata.get('total_test_cases', 0) - total_actual_cases}")
            
            # Smart selection kontrolü
            print("\n" + "=" * 50)
            print("SMART SELECTION ANALİZİ:")
            
            success_scenarios = [r for r in results if r.get('status') == 'success']
            error_scenarios = [r for r in results if r.get('status') == 'error']
            
            print(f"Başarılı scenario sayısı: {len(success_scenarios)}")
            print(f"Hatalı scenario sayısı: {len(error_scenarios)}")
            
            if error_scenarios:
                print("\nHatalı scenario'lar:")
                for err_scenario in error_scenarios:
                    print(f"  - {err_scenario.get('scenario_id')}: {err_scenario.get('error', 'Bilinmeyen hata')}")

except Exception as e:
    print(f"Hata: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        client.close()
    except:
        pass
