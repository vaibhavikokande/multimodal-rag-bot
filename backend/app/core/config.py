from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Multimodal Enterprise RAG Bot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/ragbot"
    SYNC_DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ragbot"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_EMBEDDING_DIMENSIONS: int = 3072

    # Groq (FREE - https://console.groq.com)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Anthropic (optional)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Vector DB
    VECTOR_DB_PROVIDER: str = "chromadb"  # chromadb | pinecone
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION_NAME: str = "enterprise_rag"
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_INDEX_NAME: str = "enterprise-rag"

    # File Storage
    STORAGE_PROVIDER: str = "local"  # local | s3 | gcs
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: List[str] = [
        "pdf", "docx", "doc", "pptx", "ppt", "txt", "csv", "xlsx",
        "png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp",
        "mp4", "avi", "mov", "mkv", "webm",
        "mp3", "wav", "m4a", "ogg", "flac"
    ]

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "ragbot-uploads"

    # GCS
    GCS_BUCKET_NAME: str = ""
    GCS_PROJECT_ID: str = ""

    # OCR
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    OCR_PROVIDER: str = "tesseract"  # tesseract | paddleocr

    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_CHUNKS_PER_DOC: int = 1000

    # RAG
    TOP_K_RESULTS: int = 10
    SIMILARITY_THRESHOLD: float = 0.7
    RERANK_TOP_K: int = 5
    HYBRID_SEARCH_ALPHA: float = 0.5  # 0=keyword, 1=vector

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://your-domain.com"
    ]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Monitoring
    SENTRY_DSN: str = ""
    ENABLE_PROMETHEUS: bool = True

    # Admin
    ADMIN_EMAIL: str = "admin@company.com"
    ADMIN_PASSWORD: str = "Admin@123456"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
