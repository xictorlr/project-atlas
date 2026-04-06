"use client";

import { useState, useEffect, useCallback } from "react";
import { MessageCircle, RefreshCw, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getHermesContext, clearHermesContext, type ContextEntry } from "@/lib/api";

interface HermesPanelProps {
  projectId: string;
}

export function HermesPanel({ projectId }: HermesPanelProps) {
  const [context, setContext] = useState<ContextEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [resuming, setResuming] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadContext = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getHermesContext(projectId);
      if (response.success && response.data) {
        setContext(Array.isArray(response.data) ? response.data : []);
      } else if (!response.success) {
        // Hermes might be disabled or have no context yet — soft error
        setContext([]);
        if (response.error && !response.error.includes("Not found")) {
          setError(response.error);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load context");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadContext();
  }, [loadContext]);

  async function handleResume() {
    setResuming(true);
    setError(null);
    try {
      await loadContext();
    } finally {
      setResuming(false);
    }
  }

  async function handleClear() {
    if (!confirm("Clear all Hermes context for this project? This cannot be undone.")) return;
    setClearing(true);
    setError(null);
    try {
      const response = await clearHermesContext(projectId);
      if (!response.success) {
        throw new Error(response.error || "Clear failed");
      }
      setContext([]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Clear failed");
    } finally {
      setClearing(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <MessageCircle className="h-4 w-4 text-indigo-600" />
            <h3 className="font-semibold">Hermes Context</h3>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Persistent conversation context across sessions. Resume any previous
            analytical thread.
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleResume}
            disabled={resuming}
          >
            <RefreshCw className={`mr-1 h-3 w-3 ${resuming ? "animate-spin" : ""}`} />
            Resume
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            disabled={clearing}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="mr-1 h-3 w-3" />
            Clear
          </Button>
        </div>
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      {context.length > 0 ? (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">
            {context.length} message{context.length !== 1 ? "s" : ""} in context
          </p>
          <div className="max-h-96 space-y-2 overflow-y-auto">
            {context.map((entry) => (
              <div
                key={entry.id}
                className={`rounded-md border p-3 text-sm ${
                  entry.role === "user"
                    ? "bg-muted/50"
                    : "bg-card"
                }`}
              >
                <div className="mb-1 flex items-center gap-2">
                  <Badge
                    variant={entry.role === "user" ? "secondary" : "outline"}
                    className="text-xs capitalize"
                  >
                    {entry.role}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {new Date(entry.createdAt).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm leading-relaxed">{entry.content}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <MessageCircle className="mx-auto mb-2 h-6 w-6 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No context yet.</p>
        </div>
      )}
    </div>
  );
}
