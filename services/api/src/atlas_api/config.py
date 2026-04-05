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
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    # Vault
    vault_path: str = Field(
        default="./vault",
        description="Absolute or relative path to the Markdown vault directory",
    )

    # LLM
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    default_llm_model: str = Field(default="claude-sonnet-4-6")

    # Observability
    otel_exporter_otlp_endpoint: str = Field(default="")
    otel_service_name: str = Field(default="atlas-api")


settings = Settings()
