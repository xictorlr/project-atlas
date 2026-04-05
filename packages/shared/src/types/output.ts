import type { OutputArtifactId, WorkspaceId, EvidencePackId } from "./ids.js";
import type { OutputArtifactKind } from "./enums.js";

export interface OutputArtifact {
  readonly id: OutputArtifactId;
  readonly workspaceId: WorkspaceId;
  readonly kind: OutputArtifactKind;
  readonly title: string;
  readonly storageKey: string | null;
  readonly publicUrl: string | null;
  readonly evidencePackId: EvidencePackId | null;
  readonly generatedAt: string;
  readonly model: string | null;
  readonly confidenceNotes: string | null;
  readonly sourceCount: number;
  readonly createdAt: string;
  readonly updatedAt: string;
}
