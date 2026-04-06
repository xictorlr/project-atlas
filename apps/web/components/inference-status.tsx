"use client";

import { useEffect, useState } from "react";
import { Cpu } from "lucide-react";
import { getInferenceHealth, type InferenceHealth } from "@/lib/api";
import { cn } from "@/lib/utils";

const POLL_INTERVAL_MS = 30_000;

export function InferenceStatus() {
  const [health, setHealth] = useState<InferenceHealth | null>(null);
  const [error, setError] = useState(false);

  async function fetchHealth() {
    try {
      const res = await getInferenceHealth();
      if (res.success && res.data) {
        setHealth(res.data);
        setError(false);
      } else {
        setError(true);
      }
    } catch {
      setError(true);
    }
  }

  useEffect(() => {
    void fetchHealth();
    const interval = setInterval(fetchHealth, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  if (!health && !error) return null;

  const ollamaUp = !error && (health?.ollamaReachable ?? false);

  return (
    <div className="flex items-center gap-2 rounded-md border bg-card px-3 py-1.5 text-xs">
      <Cpu className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />

      {/* Ollama status dot */}
      <span className="flex items-center gap-1">
        <span
          className={cn(
            "inline-block h-2 w-2 rounded-full",
            ollamaUp ? "bg-green-500" : "bg-red-500"
          )}
          aria-label={ollamaUp ? "Ollama reachable" : "Ollama unreachable"}
        />
        Ollama
      </span>

      {ollamaUp && health?.activeModel && (
        <>
          <span className="text-muted-foreground">·</span>
          <span className="font-medium">{health.activeModel}</span>
        </>
      )}

      {ollamaUp && health?.gpuMemoryMb != null && (
        <>
          <span className="text-muted-foreground">·</span>
          <span className="text-muted-foreground">
            {Math.round(health.gpuMemoryMb / 1024)} GB GPU
          </span>
        </>
      )}

      <span className="ml-1 rounded bg-muted px-1.5 py-0.5 font-medium text-muted-foreground">
        Edge Mode
      </span>
    </div>
  );
}
