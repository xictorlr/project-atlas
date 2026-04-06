"use client";

import { useEffect, useState } from "react";
import { Cpu, Download, Trash2, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getInferenceHealth, type ModelInfo, type InferenceHealth } from "@/lib/api";

// ---------------------------------------------------------------------------
// Mock data — replace with real API calls once endpoints are wired
// ---------------------------------------------------------------------------

const MOCK_MODELS: ModelInfo[] = [
  {
    name: "llama3.2:3b",
    size: 2_019_686_400,
    digest: "a80c4f17acd5",
    modifiedAt: new Date(Date.now() - 3 * 86_400_000).toISOString(),
  },
  {
    name: "mistral:7b",
    size: 4_113_301_504,
    digest: "61e88e884507",
    modifiedAt: new Date(Date.now() - 7 * 86_400_000).toISOString(),
  },
  {
    name: "qwen2.5:14b",
    size: 9_053_000_000,
    digest: "3b5f40f5f2cf",
    modifiedAt: new Date(Date.now() - 1 * 86_400_000).toISOString(),
  },
];

interface ModelProfile {
  id: string;
  label: string;
  description: string;
  recommendedModel: string;
  color: string;
}

const MODEL_PROFILES: ModelProfile[] = [
  {
    id: "light",
    label: "Light",
    description: "Fast responses for quick queries and chat. Uses 3–4 B models.",
    recommendedModel: "llama3.2:3b",
    color: "bg-green-100 text-green-800 border-green-200",
  },
  {
    id: "standard",
    label: "Standard",
    description: "Balanced speed and quality for most compilation tasks. Uses 7 B models.",
    recommendedModel: "mistral:7b",
    color: "bg-blue-100 text-blue-800 border-blue-200",
  },
  {
    id: "reasoning",
    label: "Reasoning",
    description: "Deep analysis and structured outputs. Uses 14 B models.",
    recommendedModel: "qwen2.5:14b",
    color: "bg-indigo-100 text-indigo-800 border-indigo-200",
  },
  {
    id: "polyglot",
    label: "Polyglot",
    description: "Multilingual source processing — Spanish, English, and more.",
    recommendedModel: "qwen2.5:14b",
    color: "bg-amber-100 text-amber-800 border-amber-200",
  },
  {
    id: "maximum",
    label: "Maximum",
    description:
      "Highest quality for final deliverables. Uses 30 B+ models (requires significant GPU VRAM).",
    recommendedModel: "llama3.1:70b",
    color: "bg-purple-100 text-purple-800 border-purple-200",
  },
];

// ---------------------------------------------------------------------------
// Mock pull — simulates progress events
// ---------------------------------------------------------------------------

function useMockPull() {
  const [progress, setProgress] = useState<number | null>(null);
  const [pulling, setPulling] = useState(false);
  const [pullError, setPullError] = useState<string | null>(null);

  function startPull(modelName: string): void {
    if (!modelName.trim()) return;
    setPulling(true);
    setPullError(null);
    setProgress(0);

    let pct = 0;
    const tick = setInterval(() => {
      pct += Math.random() * 12;
      if (pct >= 100) {
        clearInterval(tick);
        setProgress(100);
        setTimeout(() => {
          setPulling(false);
          setProgress(null);
        }, 600);
      } else {
        setProgress(Math.min(pct, 99));
      }
    }, 300);
  }

  return { progress, pulling, pullError, startPull };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function bytesToGb(bytes: number): string {
  return (bytes / 1_073_741_824).toFixed(1);
}

function modelFamily(name: string): string {
  const base = name.split(":")[0] ?? name;
  return base.charAt(0).toUpperCase() + base.slice(1);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface GpuBarProps {
  gpuMemoryMb: number;
  totalMb?: number;
}

function GpuBar({ gpuMemoryMb, totalMb = 16_384 }: GpuBarProps) {
  const pct = Math.min((gpuMemoryMb / totalMb) * 100, 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>GPU VRAM</span>
        <span>
          {Math.round(gpuMemoryMb / 1024)} GB / {Math.round(totalMb / 1024)} GB
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            pct > 85 ? "bg-red-500" : pct > 60 ? "bg-amber-500" : "bg-green-500"
          )}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={Math.round(pct)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="GPU VRAM usage"
        />
      </div>
    </div>
  );
}

interface PullBarProps {
  progress: number;
  modelName: string;
}

function PullBar({ progress, modelName }: PullBarProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Pulling {modelName}</span>
        <span>{Math.round(progress)}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
          role="progressbar"
          aria-valuenow={Math.round(progress)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Pulling ${modelName}`}
        />
      </div>
    </div>
  );
}

interface ModelRowProps {
  model: ModelInfo;
  activeModel: string | null;
  onDelete: (name: string) => void;
  deleteConfirm: string | null;
  onDeleteConfirm: (name: string | null) => void;
}

function ModelRow({
  model,
  activeModel,
  onDelete,
  deleteConfirm,
  onDeleteConfirm,
}: ModelRowProps) {
  const isActive = activeModel === model.name;

  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border bg-card px-4 py-3">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-sm">{model.name}</span>
          <Badge variant="outline" className="text-xs">
            {modelFamily(model.name)}
          </Badge>
          {isActive && (
            <Badge className="text-xs bg-green-100 text-green-800 border-green-200 hover:bg-green-100">
              Active
            </Badge>
          )}
        </div>
        <p className="mt-0.5 text-xs text-muted-foreground">
          {bytesToGb(model.size)} GB &middot; {model.digest.slice(0, 12)} &middot;{" "}
          {new Date(model.modifiedAt).toLocaleDateString()}
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        {deleteConfirm === model.name ? (
          <>
            <span className="text-xs text-destructive">Delete?</span>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => {
                onDelete(model.name);
                onDeleteConfirm(null);
              }}
            >
              Yes
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onDeleteConfirm(null)}
            >
              Cancel
            </Button>
          </>
        ) : (
          <Button
            size="sm"
            variant="ghost"
            className="text-muted-foreground hover:text-destructive"
            aria-label={`Delete ${model.name}`}
            onClick={() => onDeleteConfirm(model.name)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ModelsPage() {
  const [models, setModels] = useState<ModelInfo[]>(MOCK_MODELS);
  const [health, setHealth] = useState<InferenceHealth | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [pullInput, setPullInput] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [activeProfile, setActiveProfile] = useState("standard");

  const { progress, pulling, pullError, startPull } = useMockPull();

  useEffect(() => {
    async function loadHealth() {
      try {
        const res = await getInferenceHealth();
        if (res.success && res.data) {
          setHealth(res.data);
          setHealthError(false);
        } else {
          setHealthError(true);
        }
      } catch {
        setHealthError(true);
      }
    }
    void loadHealth();
  }, []);

  function handlePull() {
    if (!pullInput.trim() || pulling) return;
    startPull(pullInput.trim());
    // In production: call pullModel(pullInput.trim()) and stream progress
    // For now, mock model is added after "pull" completes
    const newName = pullInput.trim();
    setTimeout(() => {
      setModels((prev) => {
        if (prev.some((m) => m.name === newName)) return prev;
        const newModel: ModelInfo = {
          name: newName,
          size: Math.round(Math.random() * 8_000_000_000 + 2_000_000_000),
          digest: Math.random().toString(16).slice(2, 14),
          modifiedAt: new Date().toISOString(),
        };
        return [...prev, newModel];
      });
      setPullInput("");
    }, 4_500);
  }

  function handleDelete(name: string) {
    setModels((prev) => prev.filter((m) => m.name !== name));
  }

  const ollamaUp = !healthError && (health?.ollamaReachable ?? false);

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Model Management</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage locally installed Ollama models and configure inference
          profiles.
        </p>
      </div>

      {/* Inference health + GPU bar */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">Inference Engine</CardTitle>
            <span
              className={cn(
                "ml-auto inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium",
                ollamaUp
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              )}
            >
              {ollamaUp ? (
                <CheckCircle2 className="h-3 w-3" />
              ) : (
                <AlertTriangle className="h-3 w-3" />
              )}
              {ollamaUp ? "Ollama reachable" : "Ollama unreachable"}
            </span>
          </div>
          {ollamaUp && health?.activeModel && (
            <CardDescription>
              Active model:{" "}
              <span className="font-medium text-foreground">
                {health.activeModel}
              </span>
            </CardDescription>
          )}
        </CardHeader>
        {ollamaUp && health?.gpuMemoryMb != null && (
          <CardContent>
            <GpuBar gpuMemoryMb={health.gpuMemoryMb} />
          </CardContent>
        )}
      </Card>

      {/* Pull new model */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Pull New Model</CardTitle>
          <CardDescription>
            Enter an Ollama model name (e.g.{" "}
            <code className="rounded bg-muted px-1 text-xs">llama3.2:3b</code>
            ,{" "}
            <code className="rounded bg-muted px-1 text-xs">mistral:7b</code>).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder="model:tag"
              value={pullInput}
              onChange={(e) => setPullInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handlePull();
              }}
              disabled={pulling}
              className="max-w-xs"
              aria-label="Model name to pull"
            />
            <Button
              onClick={handlePull}
              disabled={pulling || !pullInput.trim()}
            >
              <Download className="mr-1.5 h-4 w-4" />
              {pulling ? "Pulling..." : "Pull"}
            </Button>
          </div>

          {pulling && progress !== null && (
            <PullBar progress={progress} modelName={pullInput} />
          )}

          {pullError && (
            <p className="text-sm text-destructive">{pullError}</p>
          )}
        </CardContent>
      </Card>

      {/* Installed models */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">
            Installed Models
            <Badge variant="secondary" className="ml-2">
              {models.length}
            </Badge>
          </h2>
        </div>

        {models.length === 0 ? (
          <div className="rounded-lg border border-dashed p-10 text-center">
            <p className="text-sm text-muted-foreground">
              No models installed. Pull a model above to get started.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {models.map((model) => (
              <ModelRow
                key={model.name}
                model={model}
                activeModel={health?.activeModel ?? null}
                onDelete={handleDelete}
                deleteConfirm={deleteConfirm}
                onDeleteConfirm={setDeleteConfirm}
              />
            ))}
          </div>
        )}
      </div>

      {/* Inference profiles */}
      <div className="space-y-3">
        <div>
          <h2 className="text-base font-semibold">Inference Profiles</h2>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Select the profile used when generating outputs and running
            compilations. The active profile is highlighted.
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {MODEL_PROFILES.map((profile) => {
            const isSelected = activeProfile === profile.id;
            return (
              <button
                key={profile.id}
                onClick={() => setActiveProfile(profile.id)}
                className={cn(
                  "rounded-lg border p-4 text-left transition-all",
                  isSelected
                    ? "border-primary ring-2 ring-primary ring-offset-2"
                    : "border-border hover:border-primary/50"
                )}
                aria-pressed={isSelected}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={cn(
                      "inline-block rounded px-2 py-0.5 text-xs font-semibold",
                      profile.color
                    )}
                  >
                    {profile.label}
                  </span>
                  {isSelected && (
                    <CheckCircle2 className="h-4 w-4 text-primary" />
                  )}
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {profile.description}
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Recommended:{" "}
                  <code className="rounded bg-muted px-1">
                    {profile.recommendedModel}
                  </code>
                </p>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
