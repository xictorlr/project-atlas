export const SourceKind = {
  Article: "article",
  Pdf: "pdf",
  Repository: "repository",
  ImageSet: "image_set",
  Dataset: "dataset",
  Transcript: "transcript",
  WebClip: "web_clip",
} as const;
export type SourceKind = (typeof SourceKind)[keyof typeof SourceKind];

export const SourceStatus = {
  Pending: "pending",
  Ingesting: "ingesting",
  Ready: "ready",
  Failed: "failed",
} as const;
export type SourceStatus = (typeof SourceStatus)[keyof typeof SourceStatus];

export const VaultNoteKind = {
  Source: "source",
  Entity: "entity",
  Concept: "concept",
  Index: "index",
  Timeline: "timeline",
} as const;
export type VaultNoteKind = (typeof VaultNoteKind)[keyof typeof VaultNoteKind];

export const JobKind = {
  Ingest: "ingest",
  Compile: "compile",
  Index: "index",
  Answer: "answer",
  Export: "export",
  Publish: "publish",
  HealthCheck: "health_check",
  Simulation: "simulation",
} as const;
export type JobKind = (typeof JobKind)[keyof typeof JobKind];

export const JobStatus = {
  Queued: "queued",
  Running: "running",
  Succeeded: "succeeded",
  Failed: "failed",
  Cancelled: "cancelled",
} as const;
export type JobStatus = (typeof JobStatus)[keyof typeof JobStatus];

export const OutputArtifactKind = {
  Brief: "brief",
  SlideDeck: "slide_deck",
  Chart: "chart",
  PublishedPage: "published_page",
  SimulationPackage: "simulation_package",
  Download: "download",
} as const;
export type OutputArtifactKind =
  (typeof OutputArtifactKind)[keyof typeof OutputArtifactKind];

export const WorkspaceRole = {
  Owner: "owner",
  Admin: "admin",
  Editor: "editor",
  Reviewer: "reviewer",
  Observer: "observer",
} as const;
export type WorkspaceRole = (typeof WorkspaceRole)[keyof typeof WorkspaceRole];
