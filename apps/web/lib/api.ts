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
  try {
    const res = await fetch(
      `${BASE_URL}/api/v1/workspaces/${workspaceId}/sources/upload`,
      { method: "POST", body: formData }
    );
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      let errorMsg = res.statusText;
      try {
        const parsed = JSON.parse(text);
        errorMsg = parsed.error || parsed.detail || text || res.statusText;
      } catch {
        errorMsg = text || res.statusText;
      }
      return { success: false, error: errorMsg };
    }
    const body = await res.json();
    if (body && typeof body === "object" && "success" in body && ("data" in body || "error" in body)) {
      return body as ApiResponse<Source>;
    }
    return { success: true, data: body as Source };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : "Network error",
    };
  }
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

// Projects (mapped to workspaces API — projects are workspaces in El Consultor)
export function createProject(
  data: { name: string; slug: string; description?: string; client?: string; language?: string }
): Promise<ApiResponse<Workspace>> {
  return apiFetch<Workspace>("/api/v1/workspaces", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getProjects(): Promise<ApiResponse<Workspace[]>> {
  return apiFetch<Workspace[]>("/api/v1/workspaces");
}

export function updateProject(
  id: string,
  data: Partial<{ name: string; description: string; client: string; language: string }>
): Promise<ApiResponse<Workspace>> {
  return apiFetch<Workspace>(`/api/v1/workspaces/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// Outputs
export interface OutputJob {
  jobId: string;
  kind: string;
  status: string;
  createdAt: string;
}

export function generateOutput(
  projectId: string,
  kind: string,
  params: { instructions?: string; model?: string }
): Promise<ApiResponse<OutputJob>> {
  return apiFetch<OutputJob>(`/api/v1/workspaces/${projectId}/outputs/generate`, {
    method: "POST",
    body: JSON.stringify({ kind, ...params }),
  });
}

export function getOutputs(projectId: string): Promise<ApiResponse<VaultNote[]>> {
  return apiFetch<VaultNote[]>(`/api/v1/workspaces/${projectId}/vault/notes?kind=output`);
}

// Tools — DeerFlow
export interface ToolJob {
  jobId: string;
  status: string;
  createdAt: string;
}

export function submitDeerFlowQuery(
  projectId: string,
  question: string
): Promise<ApiResponse<ToolJob>> {
  return apiFetch<ToolJob>(
    `/api/v1/workspaces/${projectId}/integrations/deerflow/submit`,
    {
      method: "POST",
      body: JSON.stringify({ question }),
    }
  );
}

export function getDeerFlowTask(
  projectId: string,
  taskId: string
): Promise<ApiResponse<ToolJob>> {
  return apiFetch<ToolJob>(
    `/api/v1/workspaces/${projectId}/integrations/deerflow/tasks/${taskId}`
  );
}

// Tools — MiroFish (currently feature-flagged off; endpoint may not exist yet)
export function submitMiroFishScenario(
  projectId: string,
  scenario: string
): Promise<ApiResponse<ToolJob>> {
  return apiFetch<ToolJob>(
    `/api/v1/workspaces/${projectId}/integrations/mirofish/submit`,
    {
      method: "POST",
      body: JSON.stringify({ scenario }),
    }
  );
}

// Tools — Hermes
export interface ContextEntry {
  id: string;
  role: string;
  content: string;
  createdAt: string;
}

export function getHermesContext(
  projectId: string
): Promise<ApiResponse<ContextEntry[]>> {
  return apiFetch<ContextEntry[]>(
    `/api/v1/workspaces/${projectId}/integrations/hermes/context`
  );
}

export function clearHermesContext(
  projectId: string
): Promise<ApiResponse<null>> {
  return apiFetch<null>(
    `/api/v1/workspaces/${projectId}/integrations/hermes/context`,
    { method: "DELETE" }
  );
}

// Models / Inference
export interface ModelInfo {
  name: string;
  size: number;
  digest: string;
  modifiedAt: string;
}

export interface PullProgress {
  status: string;
  completed?: number;
  total?: number;
}

export interface InferenceHealth {
  ollamaReachable: boolean;
  activeModel: string | null;
  gpuMemoryMb: number | null;
}

export function getModels(): Promise<ApiResponse<ModelInfo[]>> {
  return apiFetch<ModelInfo[]>("/api/v1/models");
}

export function pullModel(name: string): Promise<ApiResponse<PullProgress>> {
  return apiFetch<PullProgress>("/api/v1/models/pull", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function getInferenceHealth(): Promise<ApiResponse<InferenceHealth>> {
  return apiFetch<InferenceHealth>("/api/v1/health/inference");
}

export { apiFetch, type ApiResponse };
