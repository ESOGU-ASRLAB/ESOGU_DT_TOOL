"""
migrate_stlc_manager_to_stlc_database.py
-----------------------------------------
Safely migrates data from stlc_manager database to stlc_database.
Only adds missing data, never deletes existing data from stlc_database.
"""

from pymongo import MongoClient
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MONGO_URI = "mongodb://localhost:27017"
SOURCE_DB = "stlc_manager"
TARGET_DB = "stlc_database"

def migrate_data():
    """
    Migrates data from stlc_manager to stlc_database.
    Only adds missing documents, never deletes.
    """
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        logger.info("✓ Connected to MongoDB")
        
        source_db = client[SOURCE_DB]
        target_db = client[TARGET_DB]
        
        # Get all collections from source database
        source_collections = source_db.list_collection_names()
        logger.info(f"\n{'='*70}")
        logger.info(f"SOURCE DATABASE: {SOURCE_DB}")
        logger.info(f"Collections found: {len(source_collections)}")
        logger.info(f"{'='*70}\n")
        
        if not source_collections:
            logger.warning(f"No collections found in {SOURCE_DB}. Nothing to migrate.")
            return
        
        # Statistics
        total_collections_processed = 0
        total_docs_copied = 0
        total_docs_skipped = 0
        
        for collection_name in source_collections:
            logger.info(f"\n{'─'*70}")
            logger.info(f"Processing collection: {collection_name}")
            logger.info(f"{'─'*70}")
            
            source_collection = source_db[collection_name]
            target_collection = target_db[collection_name]
            
            # Get document counts
            source_count = source_collection.count_documents({})
            target_count_before = target_collection.count_documents({})
            
            logger.info(f"  Source ({SOURCE_DB}): {source_count} documents")
            logger.info(f"  Target ({TARGET_DB}): {target_count_before} documents (before migration)")
            
            if source_count == 0:
                logger.info(f"  ⊘ Skipping - no documents in source")
                continue
            
            # Get all documents from source
            source_docs = list(source_collection.find({}))
            
            docs_copied = 0
            docs_skipped = 0
            
            for doc in source_docs:
                # Check if document exists in target by _id
                if target_collection.find_one({"_id": doc["_id"]}):
                    docs_skipped += 1
                else:
                    # Insert missing document
                    target_collection.insert_one(doc)
                    docs_copied += 1
            
            target_count_after = target_collection.count_documents({})
            
            logger.info(f"  ✓ Migration complete:")
            logger.info(f"    • Documents copied: {docs_copied}")
            logger.info(f"    • Documents skipped (already exist): {docs_skipped}")
            logger.info(f"    • Target count after: {target_count_after}")
            
            total_collections_processed += 1
            total_docs_copied += docs_copied
            total_docs_skipped += docs_skipped
        
        # Final summary
        logger.info(f"\n{'='*70}")
        logger.info(f"MIGRATION SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Collections processed: {total_collections_processed}")
        logger.info(f"Total documents copied: {total_docs_copied}")
        logger.info(f"Total documents skipped: {total_docs_skipped}")
        logger.info(f"Target database: {TARGET_DB}")
        logger.info(f"{'='*70}\n")
        
        # Show final state of target database
        logger.info(f"Final state of {TARGET_DB}:")
        target_collections = target_db.list_collection_names()
        for col_name in sorted(target_collections):
            count = target_db[col_name].count_documents({})
            logger.info(f"  • {col_name}: {count} documents")
        
        logger.info(f"\n✓ Migration completed successfully!")
        logger.info(f"✓ No data was deleted from {TARGET_DB}")
        
    except Exception as e:
        logger.error(f"✗ Migration failed: {str(e)}")
        raise
    finally:
        client.close()
        logger.info("\n✓ MongoDB connection closed")

if __name__ == "__main__":
    logger.info(f"""
{'='*70}
DATA MIGRATION SCRIPT
{'='*70}
Source: {SOURCE_DB}
Target: {TARGET_DB}
Strategy: Add missing data only (no deletions)
{'='*70}
""")
    
    response = input(f"Proceed with migration from {SOURCE_DB} to {TARGET_DB}? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        migrate_data()
    else:
        logger.info("Migration cancelled by user.")
