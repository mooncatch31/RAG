from typing import List, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, computed_field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "kb-backend"
    APP_ENV: str = "dev"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    LOG_LEVEL: Literal["DEBUG","INFO","WARNING","ERROR","CRITICAL"] = "INFO"
    LOG_JSON: bool = False
    LOG_ACCESS: bool = True

    CORS_ALLOW_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOW_HEADERS: str = "*"
    CORS_ALLOW_METHODS: str = "*"

    DATABASE_URL: str

    OPENAI_API_KEY: str | None = None
    CHAT_MODEL: str = "gpt-4o-mini"

    EMBEDDING_PROVIDER: Literal["local","openai","ollama"] = "local"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH: int = 64
    EMBED_REQUEST_DELAY_S: float = 1.0
    EMBED_MAX_RETRIES: int = 8
    EMBED_MAX_CONCURRENCY: int = 1

    OLLAMA_BASE_URL: str = "http://localhost:11434"

    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX: str = "kb-index-local"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"

    WORKSPACE_DEFAULT: str = "default"
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 75
    MAX_CONTEXT_CHUNKS: int = 6
    TOPK: int = 20

    MAX_UPLOAD_MB: int = 25
    MAX_FILES: int = 20

    AUTO_ENRICH_ENABLED: bool = False
    AUTO_ENRICH_MIN_CONF: float = 0.2
    AUTO_ENRICH_MAX_DOCS: int = 3
    AUTO_ENRICH_MAX_PER_TOPIC: int = 1

    GOOGLE_CSE_API_KEY: str | None = None
    GOOGLE_CSE_CX: str | None = None

    @field_validator("EMBEDDING_BATCH")
    @classmethod
    def _batch_min(cls, v: int) -> int: return max(1, int(v))

    @field_validator("LOG_LEVEL")
    @classmethod
    def _lvl(cls, v: str) -> str: return v.upper()

    @computed_field  # type: ignore[misc]
    @property
    def CORS_ALLOW_ORIGINS_LIST(self) -> List[str]:
        parts = [p.strip() for p in (self.CORS_ALLOW_ORIGINS or "").split(",")]
        return [p for p in parts if p]

    @computed_field  # type: ignore[misc]
    @property
    def OPENAI_ENABLED(self) -> bool:
        return bool(self.OPENAI_API_KEY)

settings = Settings()
