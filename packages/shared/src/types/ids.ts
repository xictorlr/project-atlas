declare const __brand: unique symbol;
type Brand<T, B> = T & { readonly [__brand]: B };

export type WorkspaceId = Brand<string, "WorkspaceId">;
export type UserId = Brand<string, "UserId">;
export type SourceId = Brand<string, "SourceId">;
export type VaultNoteId = Brand<string, "VaultNoteId">;
export type EntityId = Brand<string, "EntityId">;
export type ConceptId = Brand<string, "ConceptId">;
export type EvidencePackId = Brand<string, "EvidencePackId">;
export type OutputArtifactId = Brand<string, "OutputArtifactId">;
export type JobId = Brand<string, "JobId">;

export function asWorkspaceId(s: string): WorkspaceId {
  return s as WorkspaceId;
}
export function asUserId(s: string): UserId {
  return s as UserId;
}
export function asSourceId(s: string): SourceId {
  return s as SourceId;
}
export function asVaultNoteId(s: string): VaultNoteId {
  return s as VaultNoteId;
}
export function asEntityId(s: string): EntityId {
  return s as EntityId;
}
export function asConceptId(s: string): ConceptId {
  return s as ConceptId;
}
export function asEvidencePackId(s: string): EvidencePackId {
  return s as EvidencePackId;
}
export function asOutputArtifactId(s: string): OutputArtifactId {
  return s as OutputArtifactId;
}
export function asJobId(s: string): JobId {
  return s as JobId;
}
