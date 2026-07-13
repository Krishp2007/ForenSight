import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self._clients = {}

    @property
    def client(self) -> AsyncIOMotorClient:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop not in self._clients:
            logger.info(f"Creating new AsyncIOMotorClient connection for loop {id(loop)}")
            self._clients[loop] = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000
            )
        return self._clients[loop]

    @property
    def db(self):
        c = self.client
        if c is None:
            return None
        return c[settings.MONGODB_DB_NAME]

db_client = MongoDB()

async def connect_to_mongo():
    logger.info("Initializing MongoDB connection...")
    try:
        # Access properties to trigger lazy initialization and verify connection
        client = db_client.client
        await client.server_info()
        logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    logger.info("Closing MongoDB connections...")
    loop_keys = list(db_client._clients.keys())
    for loop in loop_keys:
        try:
            db_client._clients[loop].close()
            del db_client._clients[loop]
        except Exception:
            pass
    logger.info("All MongoDB connections closed.")
