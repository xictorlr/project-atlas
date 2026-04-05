"""Domain enumerations — mirrors packages/shared/src/types/enums.ts."""

from enum import StrEnum


class SourceKind(StrEnum):
    ARTICLE = "article"
    PDF = "pdf"
    REPOSITORY = "repository"
    IMAGE_SET = "image_set"
    DATASET = "dataset"
    TRANSCRIPT = "transcript"
    WEB_CLIP = "web_clip"


class SourceStatus(StrEnum):
    PENDING = "pending"
    INGESTING = "ingesting"
    READY = "ready"
    FAILED = "failed"


class VaultNoteKind(StrEnum):
    SOURCE = "source"
    ENTITY = "entity"
    CONCEPT = "concept"
    INDEX = "index"
    TIMELINE = "timeline"


class JobKind(StrEnum):
    INGEST = "ingest"
    COMPILE = "compile"
    INDEX = "index"
    ANSWER = "answer"
    EXPORT = "export"
    PUBLISH = "publish"
    HEALTH_CHECK = "health_check"
    SIMULATION = "simulation"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutputArtifactKind(StrEnum):
    BRIEF = "brief"
    SLIDE_DECK = "slide_deck"
    CHART = "chart"
    PUBLISHED_PAGE = "published_page"
    SIMULATION_PACKAGE = "simulation_package"
    DOWNLOAD = "download"


class WorkspaceRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    OBSERVER = "observer"


class EntityKind(StrEnum):
    PERSON = "person"
    COMPANY = "company"
    PROJECT = "project"
    PAPER = "paper"
    DATASET = "dataset"
    PRODUCT = "product"
