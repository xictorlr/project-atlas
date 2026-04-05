import type { Workspace, Source, Job, VaultNote } from "@atlas/shared";
import { apiFetch, type ApiResponse } from "./api-internal";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Workspaces
export function getWorkspaces(): Promise<ApiResponse<Workspace[]>> {
  return apiFetch<Workspace[]>("/api/v1/workspaces");
}

export function getWorkspace(slug: string): Promise<ApiResponse<Workspace>> {
  return apiFetch<Workspace>(`/api/v1/workspaces/${slug}`);
}

// Sources
export function getSources(workspaceId: string): Promise<ApiResponse<Source[]>> {
  return apiFetch<Source[]>(`/api/v1/workspaces/${workspaceId}/sources`);
}

export async function createSource(
  workspaceId: string,
  formData: FormData
): Promise<ApiResponse<Source>> {
  const res = await fetch(
    `${BASE_URL}/api/v1/workspaces/${workspaceId}/sources`,
    { method: "POST", body: formData }
  );
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    return { success: false, error: text || res.statusText };
  }
  return (await res.json()) as ApiResponse<Source>;
}

export function deleteSource(
  workspaceId: string,
  sourceId: string
): Promise<ApiResponse<null>> {
  return apiFetch<null>(
    `/api/v1/workspaces/${workspaceId}/sources/${sourceId}`,
    { method: "DELETE" }
  );
}

// Jobs
export function getJobs(workspaceId: string): Promise<ApiResponse<Job[]>> {
  return apiFetch<Job[]>(`/api/v1/workspaces/${workspaceId}/jobs`);
}

export function getJob(
  workspaceId: string,
  jobId: string
): Promise<ApiResponse<Job>> {
  return apiFetch<Job>(`/api/v1/workspaces/${workspaceId}/jobs/${jobId}`);
}

// Workspace stats
export interface WorkspaceStats {
  sourceCount: number;
  noteCount: number;
  entityCount: number;
  jobCount: number;
}

export function getWorkspaceStats(
  workspaceId: string
): Promise<ApiResponse<WorkspaceStats>> {
  return apiFetch<WorkspaceStats>(`/api/v1/workspaces/${workspaceId}/stats`);
}

// Vault notes
export function getVaultNotes(
  workspaceId: string
): Promise<ApiResponse<VaultNote[]>> {
  return apiFetch<VaultNote[]>(`/api/v1/workspaces/${workspaceId}/vault/notes`);
}

export function getVaultNote(
  workspaceId: string,
  slug: string
): Promise<ApiResponse<VaultNote>> {
  return apiFetch<VaultNote>(
    `/api/v1/workspaces/${workspaceId}/vault/notes/${slug}`
  );
}

export function getVaultNoteContent(
  workspaceId: string,
  slug: string
): Promise<ApiResponse<{ content: string }>> {
  return apiFetch<{ content: string }>(
    `/api/v1/workspaces/${workspaceId}/vault/notes/${slug}/content`
  );
}

// Search
export interface SearchHit {
  noteId: string;
  slug: string;
  title: string;
  snippet: string;
  score: number;
  kind: string;
}

export function searchVault(
  workspaceId: string,
  query: string
): Promise<ApiResponse<SearchHit[]>> {
  const params = new URLSearchParams({ q: query });
  return apiFetch<SearchHit[]>(
    `/api/v1/workspaces/${workspaceId}/search?${params}`
  );
}

// Evidence
export interface Citation {
  noteId: string;
  slug: string;
  title: string;
  passage: string;
  score: number;
}

export interface EvidencePack {
  query: string;
  citations: Citation[];
  assembledAt: string;
}

export function buildEvidence(
  workspaceId: string,
  query: string,
  noteIds: string[]
): Promise<ApiResponse<EvidencePack>> {
  return apiFetch<EvidencePack>(`/api/v1/workspaces/${workspaceId}/evidence`, {
    method: "POST",
    body: JSON.stringify({ query, note_ids: noteIds }),
  });
}

export { apiFetch, type ApiResponse };
