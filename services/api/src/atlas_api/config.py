"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ATLAS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://atlas:atlas_dev_password@localhost:5432/atlas_dev",
        description="Async PostgreSQL connection string (asyncpg driver)",
    )
    database_sync_url: str = Field(
        default="postgresql://atlas:atlas_dev_password@localhost:5432/atlas_dev",
        description="Sync PostgreSQL connection string — used by Alembic migrations",
    )
    db_pool_size: int = Field(default=10)
    db_max_overflow: int = Field(default=20)
    db_pool_timeout: int = Field(default=30)

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_queue_url: str = Field(
        default="redis://localhost:6379/1",
        description="Redis DB index used for job queues",
    )

    # Auth
    secret_key: str = Field(
        default="change-me-in-production",
        description="JWT signing secret — must be overridden in production",
    )
    access_token_expire_minutes: int = Field(default=60)
    jwt_algorithm: str = Field(default="HS256")

    # App
    environment: str = Field(default="development")
    log_level: str = Field(default="info")
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:3001"])

    # Vault
    vault_path: str = Field(
        default="./vault",
        description="Absolute or relative path to the Markdown vault directory",
    )

    # Inference — edge-first (Ollama local, no cloud APIs)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama REST API URL",
    )
    ollama_default_model: str = Field(default="gemma4:26b")
    ollama_embedding_model: str = Field(default="nomic-embed-text")

    # Adapter models (each adapter can use a different model)
    deerflow_model: str = Field(default="gemma4:26b")
    hermes_model: str = Field(default="gemma4")
    mirofish_model: str = Field(default="gemma4:26b")

    # Observability
    otel_exporter_otlp_endpoint: str = Field(default="")
    otel_service_name: str = Field(default="atlas-api")

    # ── Integration feature flags ──────────────────────────────────────────────
    # Obsidian sync is enabled by default (core workflow).
    # All third-party adapters default to disabled.

    obsidian_sync_enabled: bool = Field(
        default=True,
        description="Enable Obsidian vault sync and export endpoints (ATLAS_OBSIDIAN_SYNC_ENABLED)",
    )

    deerflow_enabled: bool = Field(
        default=True,
        description="Enable DeerFlow local research adapter (ATLAS_DEERFLOW_ENABLED)",
    )
    deerflow_base_url: str = Field(
        default="",
        description="DeerFlow API base URL",
    )
    deerflow_api_key: str = Field(
        default="",
        description="DeerFlow API key — keep secret",
    )

    hermes_enabled: bool = Field(
        default=True,
        description="Enable Hermes local session memory adapter (ATLAS_HERMES_ENABLED)",
    )
    hermes_context_ttl_seconds: int = Field(
        default=3600,
        description="TTL for Hermes context entries in Redis",
    )

    mirofish_enabled: bool = Field(
        default=False,
        description="Enable MiroFish simulation gateway — isolated, requires confirmation (ATLAS_MIROFISH_ENABLED)",
    )
    mirofish_require_confirmation: bool = Field(
        default=True,
        description="Require explicit confirmation header before running simulations",
    )


settings = Settings()
