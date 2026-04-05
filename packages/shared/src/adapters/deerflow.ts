/**
 * DeerFlow agent-orchestration adapter — TypeScript interface definitions.
 *
 * This module defines the shared DTOs and interface contract used by the
 * web app and any TypeScript clients that need to communicate with the
 * Atlas DeerFlow integration endpoints.
 *
 * Feature flag: ATLAS_DEERFLOW_ENABLED (server-side only).
 * The adapter interface here mirrors the Python Protocol in
 * services/api/src/atlas_api/adapters/deerflow.py.
 *
 * Invariants (rules/80-integrations-and-licensing.md):
 *   - replaceable: depends only on the interface, not any concrete class
 *   - thin: no orchestration logic; translate between Atlas DTOs and API calls
 *   - documented: failure states described per method
 *   - optional: callers must check the feature flag before using
 *   - license-aware: DeerFlow is third-party; surface area kept minimal
 */

// ── Domain DTOs ────────────────────────────────────────────────────────────────

export interface DeerFlowTask {
  readonly workspaceId: string;
  readonly taskType: string;
  readonly payload: Record<string, unknown>;
}

export type DeerFlowTaskStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface DeerFlowTaskResult {
  readonly taskId: string;
  readonly status: DeerFlowTaskStatus;
  readonly result: Record<string, unknown> | null;
  readonly error: string | null;
}

// ── Interface ─────────────────────────────────────────────────────────────────

/**
 * Interface that all DeerFlow adapter implementations must satisfy.
 *
 * The canonical Python implementation lives in
 * services/api/src/atlas_api/adapters/deerflow.py.
 * This TypeScript interface is for client-side or SSR code that calls
 * the Atlas API rather than DeerFlow directly.
 */
export interface DeerFlowAdapter {
  /**
   * Submit a task to DeerFlow via the Atlas API.
   *
   * Failure states:
   *   - Network error: throws Error with message.
   *   - Atlas API returns non-2xx: throws Error with status.
   *   - Feature disabled (server): returns 503.
   */
  submitTask(task: DeerFlowTask): Promise<DeerFlowTaskResult>;

  /**
   * Poll the current status and result for a previously submitted task.
   *
   * Failure states:
   *   - taskId not found: result has status="failed", error="not_found".
   *   - Network error: throws Error.
   */
  getResult(taskId: string): Promise<DeerFlowTaskResult>;

  /**
   * Request cancellation of a running task.
   *
   * Failure states:
   *   - taskId not found: result has status="failed", error="not_found".
   *   - Network error: throws Error.
   */
  cancel(taskId: string): Promise<DeerFlowTaskResult>;
}

// ── API client implementation ─────────────────────────────────────────────────

/**
 * DeerFlow adapter that calls the Atlas API integration endpoints.
 *
 * This is the standard implementation for use in the web app (apps/web).
 * It does not call DeerFlow directly — that is the Python adapter's job.
 */
export class AtlasDeerFlowAdapter implements DeerFlowAdapter {
  constructor(
    private readonly baseUrl: string,
    private readonly workspaceId: string,
  ) {}

  async submitTask(task: DeerFlowTask): Promise<DeerFlowTaskResult> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/workspaces/${this.workspaceId}/integrations/deerflow/submit`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: task.taskType,
          payload: task.payload,
        }),
      },
    );
    if (!response.ok) {
      throw new Error(
        `DeerFlow submitTask failed: ${response.status} ${response.statusText}`,
      );
    }
    const body = await response.json() as { data: DeerFlowTaskResult };
    return body.data;
  }

  async getResult(taskId: string): Promise<DeerFlowTaskResult> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/workspaces/${this.workspaceId}/integrations/deerflow/tasks/${taskId}`,
    );
    if (!response.ok) {
      throw new Error(
        `DeerFlow getResult failed: ${response.status} ${response.statusText}`,
      );
    }
    const body = await response.json() as { data: DeerFlowTaskResult };
    return body.data;
  }

  async cancel(taskId: string): Promise<DeerFlowTaskResult> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/workspaces/${this.workspaceId}/integrations/deerflow/tasks/${taskId}/cancel`,
      { method: "POST" },
    );
    if (!response.ok) {
      throw new Error(
        `DeerFlow cancel failed: ${response.status} ${response.statusText}`,
      );
    }
    const body = await response.json() as { data: DeerFlowTaskResult };
    return body.data;
  }
}

// ── No-op stub for disabled/test contexts ─────────────────────────────────────

/**
 * Stub adapter that returns placeholder results without making network calls.
 * Use in tests or when ATLAS_DEERFLOW_ENABLED is false on the client side.
 */
export class DeerFlowNoopAdapter implements DeerFlowAdapter {
  async submitTask(task: DeerFlowTask): Promise<DeerFlowTaskResult> {
    return {
      taskId: "noop",
      status: "pending",
      result: { mock: true, taskType: task.taskType },
      error: null,
    };
  }

  async getResult(taskId: string): Promise<DeerFlowTaskResult> {
    return {
      taskId,
      status: "completed",
      result: { mock: true },
      error: null,
    };
  }

  async cancel(taskId: string): Promise<DeerFlowTaskResult> {
    return { taskId, status: "cancelled", result: null, error: null };
  }
}
