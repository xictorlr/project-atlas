import type { VaultNoteId, WorkspaceId, SourceId } from "./ids.js";
import type { VaultNoteKind } from "./enums.js";

export interface VaultNoteFrontmatter {
  readonly title: string;
  readonly slug: string;
  readonly kind: VaultNoteKind;
  readonly workspaceId: WorkspaceId;
  readonly sourceIds: readonly SourceId[];
  readonly generatedAt: string;
  readonly model: string | null;
  readonly confidenceNotes: string | null;
  readonly backlinks: readonly string[];
  readonly tags: readonly string[];
}

export interface VaultNote {
  readonly id: VaultNoteId;
  readonly workspaceId: WorkspaceId;
  readonly kind: VaultNoteKind;
  readonly slug: string;
  readonly vaultPath: string;
  readonly frontmatter: VaultNoteFrontmatter;
  readonly contentHash: string;
  readonly createdAt: string;
  readonly updatedAt: string;
}
