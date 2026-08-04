import hashlib

class ForensicHasher:
    @staticmethod
    def sha256_checksum(data: bytes) -> str:
        """Compute the SHA-256 hex digest of raw byte content."""
        hasher = hashlib.sha256()
        hasher.update(data)
        return hasher.hexdigest()
