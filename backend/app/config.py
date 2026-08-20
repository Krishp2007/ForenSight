import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env files
env_root = Path(__file__).resolve().parent.parent / ".env"
env_backend = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_root)
load_dotenv(dotenv_path=env_backend, override=True)

class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "temporary_default_secret_key_for_dev_change_me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # MongoDB Settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", os.getenv("MONGO_DB_NAME", "forensight"))

    # Neo4j Settings
    NEO4J_URI: str = os.getenv("NEO4J_URI", os.getenv("NEO4J_URL", "bolt://127.0.0.1:7687"))
    NEO4J_URL: str = NEO4J_URI
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
    NEO4J_USER: str = NEO4J_USERNAME
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "forensight_pass")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # MinIO Settings
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "False").lower() in ("true", "1", "yes")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "forensight-evidence")

    # LLM — Groq only
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "groq")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
    ENABLE_FALLBACK: bool = os.getenv("ENABLE_FALLBACK", "true").lower() in ("true", "1", "yes")

    # Email & SMTP / Brevo Settings
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL", "noreply@forensight.app").strip()
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME", "ForenSight Security").strip()
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://forensight-1l1k.onrender.com").strip().rstrip("/")




settings = Settings()

