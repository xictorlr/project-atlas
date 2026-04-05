"""Tests for worker job registry."""

import pytest
from atlas_worker.main import WorkerConfig


class TestWorkerConfig:
    """Test worker configuration and job registry."""

    def test_worker_config_has_functions_list(self):
        """Test that WorkerConfig defines job functions."""
        assert hasattr(WorkerConfig, 'functions')
        assert isinstance(WorkerConfig.functions, list)

    def test_worker_config_includes_expected_jobs(self):
        """Test that key job functions are registered."""
        job_names = [fn.__name__ for fn in WorkerConfig.functions]
        assert 'ingest_source' in job_names
        assert 'compile_vault' in job_names

    def test_worker_config_has_redis_settings(self):
        """Test that WorkerConfig has Redis configuration."""
        assert hasattr(WorkerConfig, 'redis_settings')
        assert WorkerConfig.redis_settings is not None

    def test_worker_config_has_job_limits(self):
        """Test that WorkerConfig has concurrency and timeout settings."""
        assert hasattr(WorkerConfig, 'max_jobs')
        assert WorkerConfig.max_jobs > 0
        assert hasattr(WorkerConfig, 'job_timeout')
        assert WorkerConfig.job_timeout > 0
