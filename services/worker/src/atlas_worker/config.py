"""Worker settings loaded from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ATLAS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://atlas:atlas@localhost:5432/atlas",
    )

    # Redis (arq queue)
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Worker concurrency
    max_jobs: int = Field(default=10)
    job_timeout: int = Field(default=300, description="Default job timeout in seconds")

    # App
    environment: str = Field(default="development")
    log_level: str = Field(default="info")

    # Project root (all .local/ paths derive from this)
    root: Path = Field(default=Path("."))

    # Ollama (LLMs + embeddings)
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_timeout_s: int = Field(default=120)
    ollama_default_model: str = Field(default="gemma4:27b")
    ollama_embedding_model: str = Field(default="nomic-embed-text")

    # MLX backends
    mlx_dir: Path = Field(default=Path(".local/mlx"))
    whisper_model_size: str = Field(default="large-v3")
    vlm_model: str = Field(default="mlx-community/gemma-4-12b-vision-4bit")

    # Storage (all inside project directory)
    upload_dir: Path = Field(default=Path(".local/uploads"))
    embeddings_dir: Path = Field(default=Path(".local/embeddings"))
    tmp_dir: Path = Field(default=Path(".local/tmp"))

    # Feature flags
    enable_llm_synthesis: bool = Field(default=True)
    enable_audio_ingest: bool = Field(default=True)
    enable_vision_extraction: bool = Field(default=True)

    # Model profile (overrides individual model settings)
    model_profile: str = Field(default="standard")


worker_settings = WorkerSettings()
