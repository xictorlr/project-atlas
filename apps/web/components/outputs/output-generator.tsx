"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { OutputArtifactKind } from "@atlas/shared";

const OUTPUT_TYPES = [
  { value: OutputArtifactKind.StatusReport, label: "Status Report" },
  { value: OutputArtifactKind.ClientBrief, label: "Client Brief" },
  { value: OutputArtifactKind.WeeklyDigest, label: "Weekly Digest" },
  { value: OutputArtifactKind.RiskRegister, label: "Risk Register" },
  { value: OutputArtifactKind.RaciMatrix, label: "RACI Matrix" },
  { value: OutputArtifactKind.FollowupEmail, label: "Follow-up Email" },
  { value: OutputArtifactKind.MermaidDiagram, label: "Mermaid Diagram" },
  { value: OutputArtifactKind.Custom, label: "Custom" },
] as const;

const MODEL_OPTIONS = [
  { value: "default", label: "Default (project model)" },
  { value: "llama3.2", label: "Llama 3.2 (fast)" },
  { value: "llama3.1:70b", label: "Llama 3.1 70B (accurate)" },
  { value: "mistral", label: "Mistral" },
];

interface OutputGeneratorProps {
  projectId: string;
  onSubmit?: (kind: string, instructions: string, model: string) => Promise<void>;
}

export function OutputGenerator({ projectId: _projectId, onSubmit }: OutputGeneratorProps) {
  const [kind, setKind] = useState<string>(OutputArtifactKind.StatusReport);
  const [instructions, setInstructions] = useState("");
  const [model, setModel] = useState("default");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      if (onSubmit) {
        await onSubmit(kind, instructions, model);
      } else {
        // Placeholder stub — API call goes here in production
        await new Promise((r) => setTimeout(r, 1000));
      }
      setSuccess(true);
      setInstructions("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4 rounded-lg border bg-card p-5">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <h3 className="font-semibold">Generate Output</h3>
      </div>

      <div className="space-y-3">
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="output-type">
            Output type
          </label>
          <select
            id="output-type"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            disabled={loading}
          >
            {OUTPUT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            className="mb-1 block text-sm font-medium"
            htmlFor="output-instructions"
          >
            Additional instructions{" "}
            <span className="text-xs font-normal text-muted-foreground">(optional)</span>
          </label>
          <textarea
            id="output-instructions"
            rows={3}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="Focus on risks in phase 2, include executive summary…"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            disabled={loading}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="output-model">
            Model
          </label>
          <select
            id="output-model"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={loading}
          >
            {MODEL_OPTIONS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}
      {success && (
        <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
          Output generation queued. It will appear in the outputs list when ready.
        </p>
      )}

      <Button
        className="w-full"
        onClick={handleGenerate}
        disabled={loading}
      >
        {loading ? "Generating…" : "Generate"}
      </Button>
    </div>
  );
}
