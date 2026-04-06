"""Vector search and RAG pipeline for the Atlas knowledge compiler.

Modules
-------
vector_store  PgVectorStore — raw pgvector CRUD and similarity search.
embedder      IncrementalEmbedder — vault-level incremental embedding sync.
rag           RAGPipeline — retrieve + generate with citations.
"""
