"use client";

import { useState } from "react";
import { FlaskConical, AlertTriangle, Clock } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { submitMiroFishScenario } from "@/lib/api";

interface SimulationEntry {
  id: string;
  scenario: string;
  result: string;
  createdAt: Date;
}

interface MiroFishPanelProps {
  projectId: string;
  onSubmit?: (projectId: string, scenario: string) => Promise<string>;
}

export function MiroFishPanel({ projectId: _projectId, onSubmit }: MiroFishPanelProps) {
  const [scenario, setScenario] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<SimulationEntry[]>([]);

  function handleConfirmChange(e: React.ChangeEvent<HTMLInputElement>) {
    setConfirmed(e.target.checked);
  }

  async function handleRun() {
    const s = scenario.trim();
    if (!s || !confirmed) return;

    setLoading(true);
    setError(null);

    try {
      let result: string;
      if (onSubmit) {
        result = await onSubmit(_projectId, s);
      } else {
        const response = await submitMiroFishScenario(_projectId, s);
        if (!response.success) {
          throw new Error(
            response.error?.includes("404")
              ? "MiroFish is currently disabled. Enable it via ATLAS_MIROFISH_ENABLED=true."
              : response.error || "Simulation failed"
          );
        }
        const job = response.data as unknown as { jobId?: string; status?: string; result?: string };
        result =
          job?.result ||
          `**Simulation queued.** Job ID: \`${job?.jobId ?? "unknown"}\`. Status: ${job?.status ?? "queued"}. Results will appear in vault/outputs/ once the chain-of-thought reasoning completes.`;
      }

      setHistory((prev) => [
        {
          id: `${Date.now()}`,
          scenario: s,
          result,
          createdAt: new Date(),
        },
        ...prev,
      ]);
      setScenario("");
      setConfirmed(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center gap-2">
          <FlaskConical className="h-4 w-4 text-amber-600" />
          <h3 className="font-semibold">MiroFish Simulation</h3>
          <Badge
            variant="outline"
            className="border-amber-400 text-xs text-amber-600"
          >
            Premium
          </Badge>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Run what-if scenario simulations. Each run is isolated and requires
          explicit confirmation before executing.
        </p>
      </div>

      {/* Warning banner */}
      <div className="flex gap-2 rounded-md border border-amber-200 bg-amber-50 p-3">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
        <p className="text-xs text-amber-700">
          Simulations run in an isolated sandbox and cannot modify vault content.
          However, they consume model credits and may take several minutes. Always
          review results critically before using them in client deliverables.
        </p>
      </div>

      <div className="space-y-3">
        <div>
          <label
            className="mb-1 block text-sm font-medium"
            htmlFor="mirofish-scenario"
          >
            Scenario
          </label>
          <textarea
            id="mirofish-scenario"
            rows={4}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="What if the supplier delays delivery by 6 weeks and the budget is reduced by 15%?"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            disabled={loading}
          />
        </div>

        <label className="flex cursor-pointer items-start gap-2 rounded-md border border-amber-200 bg-amber-50/50 p-3">
          <input
            type="checkbox"
            className="mt-0.5 h-4 w-4 accent-amber-600"
            checked={confirmed}
            onChange={handleConfirmChange}
            disabled={loading}
          />
          <span className="text-sm text-amber-800">
            I confirm I want to run this simulation. Results are estimates only and
            must not be presented as factual predictions.
          </span>
        </label>
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <Button
        className="w-full"
        onClick={handleRun}
        disabled={loading || !scenario.trim() || !confirmed}
      >
        {loading ? "Running simulation…" : "Run Simulation"}
      </Button>

      {history.length > 0 && (
        <div className="space-y-3">
          <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <Clock className="h-3 w-3" />
            Simulation history
          </p>
          {history.map((entry) => (
            <div key={entry.id} className="rounded-md border bg-card p-4">
              <p className="mb-1 text-xs font-medium text-muted-foreground">Scenario</p>
              <p className="mb-3 text-sm">{entry.scenario}</p>
              <p className="mb-1 text-xs font-medium text-muted-foreground">Result</p>
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
          <FlaskConical className="mx-auto mb-2 h-6 w-6 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No simulations run yet. Enter a scenario above to get started.
          </p>
        </div>
      )}
    </div>
  );
}
