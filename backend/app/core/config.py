from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/edurag.db"
    enable_mock_chat: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    document_storage_dir: str = "./data/documents"
    document_max_bytes: int = Field(default=50 * 1024 * 1024, ge=1)
    document_max_pages: int = Field(default=500, ge=1, le=5000)
    document_max_chunks: int = Field(default=5000, ge=1, le=20000)
    document_max_per_workspace: int = Field(default=10, ge=1, le=100)
    document_worker_enabled: bool = True
    document_job_timeout: int = Field(default=600, ge=10, le=3600)
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_cache_dir: str = "./data/models"
