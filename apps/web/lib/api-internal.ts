const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  meta?: { total: number; page: number; limit: number };
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json", ...init?.headers },
      ...init,
    });

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
    // API returns raw data; some endpoints already wrap in {success, data, error}
    if (body && typeof body === "object" && "success" in body && ("data" in body || "error" in body)) {
      return body as ApiResponse<T>;
    }
    return { success: true, data: body as T };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : "Network error",
    };
  }
}
