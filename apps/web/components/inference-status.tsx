"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Cpu } from "lucide-react";
import { getInferenceHealth } from "@/lib/api";
import { cn } from "@/lib/utils";

const POLL_INTERVAL_MS = 30_000;

interface InferenceHealthPayload {
  ollama_running?: boolean;
  ollama_url?: string;
  models_available?: string[];
  models_required?: string[];
  models_missing?: string[];
  default_model?: string;
  embedding_model?: string;
  status?: string;
  error?: string;
}

export function InferenceStatus() {
  const [health, setHealth] = useState<InferenceHealthPayload | null>(null);
  const [error, setError] = useState(false);

  async function fetchHealth() {
    try {
      const res = await getInferenceHealth();
      if (res.success && res.data) {
        setHealth(res.data as unknown as InferenceHealthPayload);
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

  const ollamaUp = !error && (health?.ollama_running ?? false);
  const activeModel = health?.default_model;
  const modelCount = health?.models_available?.length ?? 0;

  return (
    <Link
      href="/settings/models"
      className="flex items-center gap-2 rounded-md border bg-card px-3 py-1.5 text-xs transition-colors hover:bg-accent"
      title="Manage models"
    >
      <Cpu className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />

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

      {ollamaUp && activeModel && (
        <>
          <span className="text-muted-foreground">·</span>
          <span className="font-medium">{activeModel}</span>
        </>
      )}

      {ollamaUp && modelCount > 0 && (
        <>
          <span className="text-muted-foreground">·</span>
          <span className="text-muted-foreground">{modelCount} models</span>
        </>
      )}

      <span className="ml-1 rounded bg-muted px-1.5 py-0.5 font-medium text-muted-foreground">
        Edge
      </span>
    </Link>
  );
}
