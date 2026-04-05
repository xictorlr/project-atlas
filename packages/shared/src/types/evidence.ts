import type { EvidencePackId, WorkspaceId, SourceId, VaultNoteId } from "./ids.js";

export interface EvidenceExcerpt {
  readonly sourceId: SourceId;
  readonly chunkIndex: number;
  readonly text: string;
  readonly score: number;
  readonly locationHint: string | null;
}

export interface EvidencePack {
  readonly id: EvidencePackId;
  readonly workspaceId: WorkspaceId;
  readonly query: string;
  readonly excerpts: readonly EvidenceExcerpt[];
  readonly noteRefs: readonly VaultNoteId[];
  readonly model: string | null;
  readonly generatedAt: string;
}
