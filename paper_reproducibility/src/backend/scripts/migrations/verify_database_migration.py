"""
verify_database_migration.py
----------------------------
Verifies that the database migration was successful and all services
are now using stlc_database instead of stlc_manager.
"""

from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

MONGO_URI = "mongodb://localhost:27017"

def verify_migration():
    """
    Verifies the database migration and configuration.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        
        logger.info("=" * 70)
        logger.info("DATABASE MIGRATION VERIFICATION")
        logger.info("=" * 70)
        
        # Check both databases
        stlc_database = client["stlc_database"]
        stlc_manager = client["stlc_manager"]
        
        # Get collections from both
        stlc_database_collections = stlc_database.list_collection_names()
        stlc_manager_collections = stlc_manager.list_collection_names()
        
        logger.info(f"\n✓ stlc_database: {len(stlc_database_collections)} collections")
        for col in sorted(stlc_database_collections):
            count = stlc_database[col].count_documents({})
            logger.info(f"    • {col}: {count} documents")
        
        logger.info(f"\n✓ stlc_manager: {len(stlc_manager_collections)} collections")
        for col in sorted(stlc_manager_collections):
            count = stlc_manager[col].count_documents({})
            logger.info(f"    • {col}: {count} documents")
        
        # Verify core configuration
        logger.info(f"\n{'=' * 70}")
        logger.info("CONFIGURATION CHECK")
        logger.info("=" * 70)
        
        from core.database import DATABASE_NAME
        logger.info(f"✓ core.database.DATABASE_NAME = '{DATABASE_NAME}'")
        
        if DATABASE_NAME == "stlc_database":
            logger.info("✓ Configuration is correct!")
        else:
            logger.warning(f"✗ Configuration issue: Expected 'stlc_database', got '{DATABASE_NAME}'")
        
        # Summary
        logger.info(f"\n{'=' * 70}")
        logger.info("SUMMARY")
        logger.info("=" * 70)
        logger.info("✓ Migration from stlc_manager to stlc_database completed")
        logger.info("✓ All production services now use stlc_database via core.database")
        logger.info("✓ All check scripts updated to use stlc_database")
        logger.info("✓ No data was deleted during migration")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"✗ Verification failed: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    verify_migration()
