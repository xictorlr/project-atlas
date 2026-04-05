# Test Infrastructure Setup

This document describes the test configuration and sample tests for Project Atlas.

## Overview

Test infrastructure is set up across all services and packages with 80%+ coverage target per project requirements.

### Test Runners

- **TypeScript/JavaScript**: vitest
- **Python**: pytest with pytest-asyncio
- **Root**: turbo orchestrates all tests via `pnpm test`

## Layer-by-Layer Setup

### 1. apps/web (Next.js + React)

**Config**: `vitest.config.ts`
- Environment: jsdom (browser-like)
- Globals enabled for `describe`, `it`, `expect`
- Coverage: v8 provider with HTML reports
- Testing library: @testing-library/react

**Tests**: `app/__tests__/page.test.tsx`
- Tests landing page component rendering
- Verifies heading, description text, layout classes
- Demonstrates component testing pattern

**Scripts**:
- `pnpm test` — run tests once
- `pnpm test:watch` — watch mode
- `pnpm test:coverage` — coverage report

### 2. services/api (FastAPI)

**Config**: `pyproject.toml [tool.pytest.ini_options]`
- `asyncio_mode = "auto"`
- Test discovery from `tests/` directory

**Fixtures**: `tests/conftest.py`
- `async_client` — AsyncClient with ASGITransport for testing FastAPI endpoints
- Uses httpx for async HTTP testing

**Tests**: `tests/test_health.py`
- `test_health_returns_ok` — verifies /health endpoint returns correct schema
- `test_health_ready_endpoint_exists` — readiness probe accepts 200 or 503

**Scripts**:
- `pytest` or `uv run pytest` — run all tests
- `pytest --cov=src` — coverage report
- `pytest -v` — verbose output

### 3. services/worker (Python arq job runner)

**Config**: `pyproject.toml [tool.pytest.ini_options]`
- Same async configuration as API
- Test discovery from `tests/` directory

**Fixtures**: `tests/conftest.py`
- `worker_ctx` — minimal arq context stub for job function tests

**Tests**: `tests/test_jobs.py`
- Verifies WorkerConfig.functions list is populated
- Confirms job names match registry (ingest_source, compile_vault)
- Validates Redis settings and concurrency limits

**Scripts**:
- `pytest` — run all tests

### 4. packages/shared (TypeScript utility types and guards)

**Config**: `vitest.config.ts`
- Environment: node (no browser)
- Globals enabled
- Coverage: v8 provider

**Tests**: `src/__tests__/ids.test.ts`
- Tests branded type guard functions from `src/types/ids.ts`
- Validates all ID type converters (WorkspaceId, UserId, etc.)
- Demonstrates type guard pattern

**Scripts**:
- `pnpm test` — run tests once
- `pnpm test:watch` — watch mode

## Running All Tests

From root:
```bash
pnpm test
```

This runs:
1. apps/web vitest
2. services/api pytest
3. services/worker pytest
4. packages/shared vitest

All test results are aggregated by turbo.

## Test Coverage Target

- Global requirement: **80% minimum coverage**
- Each service/package should track coverage via their CI pipeline
- Use `--cov` flags on pytest and vitest for coverage reports

## Key Files

| Layer | Config | Tests | Fixtures |
|-------|--------|-------|----------|
| Web | apps/web/vitest.config.ts | app/__tests__/page.test.tsx | — |
| API | services/api/pyproject.toml | services/api/tests/test_health.py | services/api/tests/conftest.py |
| Worker | services/worker/pyproject.toml | services/worker/tests/test_jobs.py | services/worker/tests/conftest.py |
| Shared | packages/shared/vitest.config.ts | packages/shared/src/__tests__/ids.test.ts | — |

## Development Workflow

1. **Write test first** (RED)
2. **Run test** to see failure
3. **Implement** minimal code to pass (GREEN)
4. **Refactor** and verify (IMPROVE)
5. **Check coverage** — `pnpm test:coverage` or `pytest --cov`

## Verification Checklist

- [x] Web app tests runnable with vitest
- [x] API tests runnable with pytest + async client
- [x] Worker tests runnable with pytest
- [x] Shared package tests runnable with vitest
- [x] Root test script orchestrates all via turbo
- [x] All config files present and properly formatted
- [x] Sample tests demonstrate patterns for each layer
