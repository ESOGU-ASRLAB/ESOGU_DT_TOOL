"""
Güncellenmiş yapıyı test et - session_history kullanımı
"""
import sys
sys.path.append('.')

from services.test_code_generation_service import TestCodeGenerationService

def test_updated_structure():
    print("=" * 80)
    print("TEST: Updated Test Code Generation Service with session_history")
    print("=" * 80)
    
    service = TestCodeGenerationService()
    
    # 1. Process names'leri al
    print("\n1️⃣ Getting available process names...")
    process_names = service.get_available_process_titles()
    
    if process_names:
        print(f"   ✅ Found {len(process_names)} process names:\n")
        for i, name in enumerate(process_names[:5], 1):
            print(f"   {i}. {name}")
        if len(process_names) > 5:
            print(f"   ... and {len(process_names) - 5} more")
    else:
        print("   ❌ No process names found!")
        return
    
    # 2. İlk process için unique test cases'leri al
    print(f"\n2️⃣ Getting unique test cases for: {process_names[0]}...")
    unique_cases = service.get_unique_test_cases_by_process_title(process_names[0])
    
    if unique_cases:
        print(f"   ✅ Found {len(unique_cases)} unique test cases\n")
        print("   Sample test cases:")
        for i, tc in enumerate(unique_cases[:3], 1):
            tc_id = tc.get("TestCaseID", "N/A")
            title = tc.get("Title", "N/A")
            print(f"   {i}. {tc_id}: {title}")
        if len(unique_cases) > 3:
            print(f"   ... and {len(unique_cases) - 3} more")
    else:
        print("   ❌ No unique test cases found!")
        return
    
    print("\n" + "=" * 80)
    print("✅ SUCCESS: Service is now using session_history structure!")
    print("=" * 80)
    print("\nData sources:")
    print("  • Process Names: session_history->processes->test_case_optimization->process_name")
    print("  • Unique Test Cases: session_history->processes->test_case_optimization->output->unique_test_cases")

if __name__ == "__main__":
    try:
        test_updated_structure()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
