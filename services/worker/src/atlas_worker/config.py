"""Worker settings loaded from environment variables."""

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


worker_settings = WorkerSettings()
