import logging
import redis.asyncio as aioredis
from backend.app.config import settings

logger = logging.getLogger(__name__)

class RedisDB:
    client: aioredis.Redis = None

redis_client = RedisDB()

async def connect_to_redis():
    logger.info("Connecting to Redis...")
    try:
        redis_client.client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.client.ping()
        logger.info("Successfully connected to Redis!")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e

async def close_redis_connection():
    logger.info("Closing Redis connection...")
    if redis_client.client:
        await redis_client.client.close()
        logger.info("Redis connection closed.")
