"""Search domain models for the lexical search engine."""

from pydantic import BaseModel, ConfigDict


class SearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    note_path: str
    slug: str
    title: str
    note_type: str
    tags: tuple[str, ...]
    score: float
    snippet: str


class SearchResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    query: str
    total: int
    results: tuple[SearchResult, ...]


class LinkGraphNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    slug: str
    title: str
    note_type: str
    vault_path: str


class LinkGraphEdge(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    target: str


class LinkGraph(BaseModel):
    model_config = ConfigDict(frozen=True)

    workspace_id: str
    nodes: tuple[LinkGraphNode, ...]
    edges: tuple[LinkGraphEdge, ...]
