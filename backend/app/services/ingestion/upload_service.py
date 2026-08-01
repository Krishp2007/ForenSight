"""
Upload Service — ForenSight AI
================================
Encapsulates the MinIO file-upload logic that was previously inlined in
the evidence API endpoint. Extracting it here makes the API handler thin
and makes the upload logic independently testable.

Usage:
    from backend.app.services.ingestion.upload_service import UploadService

    object_name, sha256, size = await UploadService.store(
        file_bytes=raw_bytes,
        filename="memory.dmp",
        org_id="abc123",
        case_id="def456",
    )
"""

import hashlib
import io
import logging
from typing import Tuple

from backend.app.db.minio import minio_client
from backend.app.config import settings

logger = logging.getLogger(__name__)


class UploadService:
    """Handles hashing, deduplication check, and MinIO upload for evidence files."""

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Return the hex SHA-256 digest of raw bytes."""
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def build_object_name(
        cls, org_id: str, case_id: str, sha256: str, filename: str
    ) -> str:
        """
        Construct the MinIO object path:
          <org_id>/<case_id>/<sha256>.<ext>
        """
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
        return f"{org_id}/{case_id}/{sha256}.{ext}"

    @classmethod
    def upload(
        cls,
        file_bytes: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
    ) -> int:
        """
        Upload raw bytes to MinIO under the given object name.
        Returns the number of bytes uploaded.
        Raises an exception if the upload fails.
        """
        buf = io.BytesIO(file_bytes)
        try:
            minio_client.client.put_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=object_name,
                data=buf,
                length=len(file_bytes),
                content_type=content_type,
            )
            logger.info(
                f"[UploadService] Uploaded {len(file_bytes):,} bytes → {object_name}"
            )
        except Exception as exc:
            logger.error(f"[UploadService] MinIO upload failed: {exc}")
            raise
        return len(file_bytes)

    @classmethod
    def store(
        cls,
        file_bytes: bytes,
        filename: str,
        org_id: str,
        case_id: str,
        content_type: str = "application/octet-stream",
    ) -> Tuple[str, str, int]:
        """
        Hash, build the object path, and upload in one call.

        Returns:
            (object_name, sha256_hex, size_bytes)
        """
        sha256 = cls.compute_sha256(file_bytes)
        object_name = cls.build_object_name(org_id, case_id, sha256, filename)
        size = cls.upload(file_bytes, object_name, content_type)
        return object_name, sha256, size

    @classmethod
    def download(cls, object_name: str) -> bytes:
        """
        Download a file from MinIO by object name and return raw bytes.
        Used by the processing pipeline to retrieve files for parsing.
        """
        try:
            response = minio_client.client.get_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=object_name,
            )
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(
                f"[UploadService] Downloaded {len(data):,} bytes ← {object_name}"
            )
            return data
        except Exception as exc:
            logger.error(f"[UploadService] MinIO download failed: {exc}")
            raise
