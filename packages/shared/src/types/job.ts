import type { JobId, WorkspaceId } from "./ids.js";
import type { JobKind, JobStatus } from "./enums.js";

export interface JobError {
  readonly code: string;
  readonly message: string;
  readonly retryable: boolean;
}

export interface Job {
  readonly id: JobId;
  readonly workspaceId: WorkspaceId;
  readonly kind: JobKind;
  readonly status: JobStatus;
  readonly payload: Readonly<Record<string, unknown>>;
  readonly result: Readonly<Record<string, unknown>> | null;
  readonly error: JobError | null;
  readonly attempt: number;
  readonly maxAttempts: number;
  readonly queuedAt: string;
  readonly startedAt: string | null;
  readonly completedAt: string | null;
}
