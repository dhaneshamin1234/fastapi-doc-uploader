from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    try:
        mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongodb.database = mongodb.client[settings.DATABASE_NAME]
        
        # Test connection
        await mongodb.client.admin.command('ping')
        logger.info("Connected to MongoDB")
        # Ensure indexes
        await ensure_indexes()
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB")

async def get_database():
    """Get database instance"""
    return mongodb.database


async def ensure_indexes():
    """Create required indexes for collections"""
    db = mongodb.database
    if db is None:
        return
    # Documents collection indexes
    await db.documents.create_index("document_id", unique=True)
    await db.documents.create_index("upload_timestamp")
    await db.documents.create_index("file_hash")
    await db.documents.create_index([("filename", 1), ("upload_timestamp", -1)])