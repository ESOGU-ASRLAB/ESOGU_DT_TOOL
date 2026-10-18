import asyncio
from core.database import get_database
import json

async def debug_data_structure():
    try:
        db = await get_database()
        collection = db["session_history"]
        
        # Get both documents to see the structure
        session_ids = ["1af31fc5-0994-4314-871c-27df6ce8f10a", "d4dfc6a0-442e-4d2f-ac5b-cd85547d8d20"]
        
        for session_id in session_ids:
            print(f"\n=== ANALYZING SESSION: {session_id} ===")
            document = await collection.find_one({
                "session_id": session_id,
                "processes.test_scenario_generation": {"$exists": True}
            })
            
            if document:
                test_scenario_process = document.get("processes", {}).get("test_scenario_generation", {})
                output = test_scenario_process.get("output", {})
                metadata = output.get("metadata", {})
                
                print(f"Process title: {test_scenario_process.get('process_title', 'NOT FOUND')}")
                print(f"Has metadata: {'metadata' in output}")
                if metadata:
                    print(f"Metadata keys: {list(metadata.keys())}")
                    print(f"Test type: {metadata.get('test_type', 'NOT FOUND')}")
                    print(f"Test category: {metadata.get('test_category', 'NOT FOUND')}")
                else:
                    print("No metadata found")
                    print(f"Output keys: {list(output.keys())}")
            else:
                print(f"Document not found for session {session_id}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_data_structure())
