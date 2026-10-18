import asyncio
from core.database import get_database
import json

async def check_prompt_collection():
    try:
        db = await get_database()
        collection = db["test_scenario_generation_prompt"]
        
        print("=== TEST_SCENARIO_GENERATION_PROMPT COLLECTION ===")
        
        # Get all documents to see the structure
        cursor = collection.find({})
        documents = await cursor.to_list(length=None)
        
        print(f"Found {len(documents)} documents")
        
        for i, doc in enumerate(documents):
            print(f"\n--- Document {i+1} ---")
            print(f"Keys: {list(doc.keys())}")
            if 'test_name' in doc:
                print(f"test_name: {doc['test_name']}")
            if 'test_case_main_prompt' in doc:
                print(f"test_case_main_prompt (first 200 chars): {str(doc['test_case_main_prompt'])[:200]}...")
            print(f"Full document: {json.dumps(doc, indent=2, default=str)}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_prompt_collection())
