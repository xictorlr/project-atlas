import type { SourceId, WorkspaceId } from "./ids.js";
import type { SourceKind, SourceStatus } from "./enums.js";

export interface SourceManifest {
  readonly ingestedAt: string;
  readonly normalizedAt: string | null;
  readonly originUrl: string | null;
  readonly mimeType: string | null;
  readonly fileSizeBytes: number | null;
  readonly chunkCount: number | null;
  readonly model: string | null;
  readonly confidenceNotes: string | null;
  readonly needsReingest?: boolean;
}

export interface Source {
  readonly id: SourceId;
  readonly workspaceId: WorkspaceId;
  readonly kind: SourceKind;
  readonly status: SourceStatus;
  readonly title: string;
  readonly description: string | null;
  readonly storageKey: string;
  readonly manifest: SourceManifest | null;
  readonly createdAt: string;
  readonly updatedAt: string;
}
