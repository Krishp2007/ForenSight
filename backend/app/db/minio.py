import logging
from minio import Minio
from backend.app.config import settings

logger = logging.getLogger(__name__)

class MinioDB:
    client: Minio = None

minio_client = MinioDB()

def connect_to_minio():
    logger.info("Connecting to MinIO...")
    try:
        minio_client.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE.lower() == 'true' if isinstance(settings.MINIO_SECURE, str) else settings.MINIO_SECURE
        )
        # Test connection by listing buckets
        minio_client.client.list_buckets()
        
        # Auto-create case evidence bucket if it doesn't exist
        bucket_name = settings.MINIO_BUCKET_NAME
        if not minio_client.client.bucket_exists(bucket_name):
            minio_client.client.make_bucket(bucket_name)
            logger.info(f"Created MinIO bucket: '{bucket_name}'")
            
        logger.info("Successfully connected to MinIO!")
    except Exception as e:
        logger.error(f"Failed to connect to MinIO: {e}")
        raise e
