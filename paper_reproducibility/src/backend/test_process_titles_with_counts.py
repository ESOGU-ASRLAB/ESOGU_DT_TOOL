import requests
import json

# Backend endpoint'ini test et
url = "http://localhost:8000/api/processes/test-code-generation/process-titles"

try:
    print(f"Testing: {url}")
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse Data:")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    print(f"\n✅ Total processes: {len(data)}")
    if data:
        print(f"\nFirst 3 examples:")
        for i, item in enumerate(data[:3], 1):
            if isinstance(item, dict):
                print(f"{i}. {item.get('process_name', 'N/A')} - {item.get('test_case_count', 0)} test cases")
            else:
                print(f"{i}. {item} (old format)")
                
except Exception as e:
    print(f"❌ Error: {str(e)}")
