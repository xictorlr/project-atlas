"""Add pgvector extension and note_embeddings table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-06
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── pgvector extension ───────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── note_embeddings ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE note_embeddings (
            id            BIGSERIAL PRIMARY KEY,
            workspace_id  TEXT      NOT NULL,
            note_slug     TEXT      NOT NULL,
            note_title    TEXT,
            chunk_idx     INTEGER   NOT NULL,
            chunk_text    TEXT      NOT NULL,
            content_hash  TEXT      NOT NULL,
            embedding     vector(768) NOT NULL,
            model         TEXT      NOT NULL DEFAULT 'nomic-embed-text',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_note_embeddings_chunk
                UNIQUE (workspace_id, note_slug, chunk_idx)
        )
    """)

    # HNSW index for cosine-similarity ANN search
    op.execute("""
        CREATE INDEX idx_embeddings_hnsw
            ON note_embeddings
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 128)
    """)

    # Workspace filter index (used by all tenant-scoped queries)
    op.execute("""
        CREATE INDEX idx_embeddings_workspace
            ON note_embeddings (workspace_id)
    """)

    # Composite index for idempotent upserts and staleness checks
    op.execute("""
        CREATE INDEX idx_embeddings_hash
            ON note_embeddings (workspace_id, note_slug, content_hash)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS note_embeddings")
    op.execute("DROP EXTENSION IF EXISTS vector")
