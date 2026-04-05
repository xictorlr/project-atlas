import type { EntityId, WorkspaceId, VaultNoteId, SourceId } from "./ids.js";

export const EntityKind = {
  Person: "person",
  Company: "company",
  Project: "project",
  Paper: "paper",
  Dataset: "dataset",
  Product: "product",
} as const;
export type EntityKind = (typeof EntityKind)[keyof typeof EntityKind];

export interface Entity {
  readonly id: EntityId;
  readonly workspaceId: WorkspaceId;
  readonly kind: EntityKind;
  readonly name: string;
  readonly slug: string;
  readonly aliases: readonly string[];
  readonly vaultNoteId: VaultNoteId | null;
  readonly sourceIds: readonly SourceId[];
  readonly createdAt: string;
  readonly updatedAt: string;
}
