import logging
from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db_client = MongoDB()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    try:
        db_client.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000
        )
        db_client.db = db_client.client[settings.MONGODB_DB_NAME]
        # Trigger connection check
        await db_client.client.server_info()
        logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db_client.client:
        db_client.client.close()
        logger.info("MongoDB connection closed.")
