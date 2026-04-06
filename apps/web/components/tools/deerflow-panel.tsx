"use client";

import { useState } from "react";
import { Search, Clock } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface QueryEntry {
  id: string;
  question: string;
  result: string;
  createdAt: Date;
}

interface DeerFlowPanelProps {
  projectId: string;
  onSubmit?: (projectId: string, question: string) => Promise<string>;
}

export function DeerFlowPanel({ projectId: _projectId, onSubmit }: DeerFlowPanelProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<QueryEntry[]>([]);

  async function handleResearch() {
    const q = question.trim();
    if (!q) return;

    setLoading(true);
    setError(null);

    try {
      let result: string;
      if (onSubmit) {
        result = await onSubmit(_projectId, q);
      } else {
        // Stub — replace with actual API call in production
        await new Promise((r) => setTimeout(r, 1200));
        result =
          "**Research queued.** Results will be compiled and added to the vault once the DeerFlow job completes. Check the Jobs tab for progress.";
      }

      setHistory((prev) => [
        {
          id: `${Date.now()}`,
          question: q,
          result,
          createdAt: new Date(),
        },
        ...prev,
      ]);
      setQuestion("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Research failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-blue-600" />
          <h3 className="font-semibold">DeerFlow Research</h3>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Ask DeerFlow to run autonomous web research on any topic and compile the
          results into the vault.
        </p>
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="What should DeerFlow research?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !loading && handleResearch()}
          disabled={loading}
          className="flex-1"
        />
        <Button onClick={handleResearch} disabled={loading || !question.trim()}>
          {loading ? "Running…" : "Research"}
        </Button>
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      {history.length > 0 && (
        <div className="space-y-3">
          <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <Clock className="h-3 w-3" />
            Query history
          </p>
          {history.map((entry) => (
            <div key={entry.id} className="rounded-md border bg-card p-4">
              <p className="mb-2 text-sm font-medium">{entry.question}</p>
              <div className="prose prose-sm max-w-none text-sm">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {entry.result}
                </ReactMarkdown>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {entry.createdAt.toLocaleTimeString()}
              </p>
            </div>
          ))}
        </div>
      )}

      {history.length === 0 && !loading && (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <Search className="mx-auto mb-2 h-6 w-6 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No research queries yet. Ask something above to get started.
          </p>
        </div>
      )}
    </div>
  );
}
