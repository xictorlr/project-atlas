import { describe, it, expect } from 'vitest';
import {
  asWorkspaceId,
  asUserId,
  asSourceId,
  asVaultNoteId,
  asEntityId,
  asConceptId,
  asEvidencePackId,
  asOutputArtifactId,
  asJobId,
} from '../types/ids';

describe('ID type guards', () => {
  it('asWorkspaceId converts string to WorkspaceId', () => {
    const id = asWorkspaceId('ws-123');
    expect(id).toBe('ws-123');
  });

  it('asUserId converts string to UserId', () => {
    const id = asUserId('user-456');
    expect(id).toBe('user-456');
  });

  it('asSourceId converts string to SourceId', () => {
    const id = asSourceId('src-789');
    expect(id).toBe('src-789');
  });

  it('asVaultNoteId converts string to VaultNoteId', () => {
    const id = asVaultNoteId('note-abc');
    expect(id).toBe('note-abc');
  });

  it('asEntityId converts string to EntityId', () => {
    const id = asEntityId('entity-def');
    expect(id).toBe('entity-def');
  });

  it('asConceptId converts string to ConceptId', () => {
    const id = asConceptId('concept-ghi');
    expect(id).toBe('concept-ghi');
  });

  it('asEvidencePackId converts string to EvidencePackId', () => {
    const id = asEvidencePackId('evidence-jkl');
    expect(id).toBe('evidence-jkl');
  });

  it('asOutputArtifactId converts string to OutputArtifactId', () => {
    const id = asOutputArtifactId('output-mno');
    expect(id).toBe('output-mno');
  });

  it('asJobId converts string to JobId', () => {
    const id = asJobId('job-pqr');
    expect(id).toBe('job-pqr');
  });
});
