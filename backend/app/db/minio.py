import logging
from minio import Minio
from backend.app.config import settings

logger = logging.getLogger(__name__)

class MinioDB:
    def __init__(self):
        self._client = None

    @property
    def client(self) -> Minio:
        if self._client is None:
            logger.info("Initializing lazy MinIO connection...")
            try:
                self._client = Minio(
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE.lower() == 'true' if isinstance(settings.MINIO_SECURE, str) else settings.MINIO_SECURE
                )
                # Test connection by listing buckets
                self._client.list_buckets()
                
                # Auto-create case evidence bucket if it doesn't exist
                bucket_name = settings.MINIO_BUCKET_NAME
                if not self._client.bucket_exists(bucket_name):
                    self._client.make_bucket(bucket_name)
                    logger.info(f"Created MinIO bucket: '{bucket_name}'")
                    
                logger.info("Successfully connected to MinIO!")
            except Exception as e:
                logger.error(f"Failed to connect to MinIO: {e}")
                self._client = None
                raise e
        return self._client

minio_client = MinioDB()

def connect_to_minio():
    logger.info("Connecting to MinIO...")
    # Just access the property to trigger the connection
    _ = minio_client.client
