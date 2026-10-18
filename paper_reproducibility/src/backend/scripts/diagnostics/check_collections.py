from core.database import get_db

def check_database_collections():
    db = get_db()
    
    print('=== Database Collections ===')
    collections = db.list_collection_names()
    print(f'Available collections: {collections}')
    
    for collection_name in collections:
        collection = db[collection_name]
        count = collection.count_documents({})
        print(f'  {collection_name}: {count} documents')
        
        # If this is a collection with documents, show a sample
        if count > 0 and count < 10:
            print(f'    Sample document keys: {list(collection.find_one().keys())}')

if __name__ == "__main__":
    check_database_collections()
