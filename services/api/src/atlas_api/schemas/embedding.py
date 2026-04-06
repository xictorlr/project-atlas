"""SQLAlchemy ORM row for note embedding records (pgvector)."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from atlas_api.db import Base


class NoteEmbeddingRow(Base):
    """One embedding chunk per vault note passage.

    Each note is split into ~512-token passages; this table stores one row
    per (workspace_id, note_slug, chunk_idx) triple.  The HNSW index on
    `embedding` enables sub-millisecond cosine-similarity search.
    """

    __tablename__ = "note_embeddings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    note_slug: Mapped[str] = mapped_column(Text, nullable=False)
    note_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False, default="nomic-embed-text")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "note_slug", "chunk_idx", name="uq_note_embeddings_chunk"),
    )
