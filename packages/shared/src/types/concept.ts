import type { ConceptId, WorkspaceId, VaultNoteId, SourceId } from "./ids.js";

export interface Concept {
  readonly id: ConceptId;
  readonly workspaceId: WorkspaceId;
  readonly name: string;
  readonly slug: string;
  readonly summary: string | null;
  readonly vaultNoteId: VaultNoteId | null;
  readonly sourceIds: readonly SourceId[];
  readonly generatedAt: string | null;
  readonly model: string | null;
  readonly createdAt: string;
  readonly updatedAt: string;
}
