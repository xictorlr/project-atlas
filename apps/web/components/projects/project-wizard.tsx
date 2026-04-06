"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { MultiUploader, type UploadFile } from "@/components/sources/multi-uploader";
import { cn } from "@/lib/utils";

interface WizardState {
  // Step 1
  name: string;
  client: string;
  description: string;
  language: string;
  // Step 2
  files: UploadFile[];
  // Step 3
  modelProfile: string;
  enableDeerFlow: boolean;
  enableHermes: boolean;
  enableMiroFish: boolean;
}

const INITIAL_STATE: WizardState = {
  name: "",
  client: "",
  description: "",
  language: "es",
  files: [],
  modelProfile: "standard",
  enableDeerFlow: true,
  enableHermes: true,
  enableMiroFish: false,
};

const STEPS = ["Name & Description", "Add Sources", "Configure", "Review & Create"];

const LANGUAGE_OPTIONS = [
  { value: "es", label: "Spanish" },
  { value: "en", label: "English" },
  { value: "fr", label: "French" },
  { value: "pt", label: "Portuguese" },
  { value: "de", label: "German" },
];

const MODEL_PROFILES = [
  { value: "standard", label: "Standard" },
  { value: "fast", label: "Fast (smaller model)" },
  { value: "accurate", label: "Accurate (larger model)" },
];

export function ProjectWizard() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [state, setState] = useState<WizardState>(INITIAL_STATE);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof WizardState>(key: K, value: WizardState[K]) {
    setState((prev) => ({ ...prev, [key]: value }));
  }

  function canAdvance(): boolean {
    if (step === 0) return state.name.trim().length > 0;
    return true;
  }

  function goNext() {
    if (canAdvance() && step < STEPS.length - 1) {
      setStep((s) => s + 1);
    }
  }

  function goBack() {
    if (step > 0) setStep((s) => s - 1);
  }

  async function handleCreate() {
    setSubmitting(true);
    setError(null);
    try {
      const { createProject } = await import("@/lib/api");
      const slugified = name
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
      const result = await createProject({
        name: name.trim(),
        slug: slugified,
        description: description.trim() || undefined,
        client: client.trim() || undefined,
        language,
      });
      if (!result.success) {
        setError(result.error || "Failed to create project");
        return;
      }
      router.push("/projects");
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      {/* Step indicator */}
      <div className="mb-8 flex items-center justify-between">
        {STEPS.map((label, i) => (
          <div key={label} className="flex flex-1 items-center">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold transition-colors",
                  i < step
                    ? "bg-primary text-primary-foreground"
                    : i === step
                    ? "bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2"
                    : "bg-muted text-muted-foreground"
                )}
              >
                {i < step ? <Check className="h-4 w-4" /> : i + 1}
              </div>
              <span className="mt-1 hidden text-center text-xs text-muted-foreground sm:block">
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  "mx-2 h-0.5 flex-1",
                  i < step ? "bg-primary" : "bg-muted"
                )}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step content */}
      <div className="rounded-lg border bg-card p-6 shadow-sm">
        {step === 0 && (
          <Step1
            name={state.name}
            client={state.client}
            description={state.description}
            language={state.language}
            onChange={update}
          />
        )}
        {step === 1 && (
          <Step2
            files={state.files}
            onFilesChange={(files) => update("files", files)}
          />
        )}
        {step === 2 && (
          <Step3
            modelProfile={state.modelProfile}
            enableDeerFlow={state.enableDeerFlow}
            enableHermes={state.enableHermes}
            enableMiroFish={state.enableMiroFish}
            onChange={update}
          />
        )}
        {step === 3 && <Step4 state={state} error={error} />}
      </div>

      {/* Navigation */}
      <div className="mt-6 flex items-center justify-between">
        <Button
          variant="outline"
          onClick={goBack}
          disabled={step === 0 || submitting}
        >
          <ChevronLeft className="mr-1 h-4 w-4" />
          Back
        </Button>

        {step < STEPS.length - 1 ? (
          <Button onClick={goNext} disabled={!canAdvance()}>
            Next
            <ChevronRight className="ml-1 h-4 w-4" />
          </Button>
        ) : (
          <Button onClick={handleCreate} disabled={submitting}>
            {submitting ? "Creating..." : "Create Project"}
          </Button>
        )}
      </div>
    </div>
  );
}

// ─── Step sub-components ────────────────────────────────────────────────────

interface Step1Props {
  name: string;
  client: string;
  description: string;
  language: string;
  onChange: <K extends keyof WizardState>(key: K, value: WizardState[K]) => void;
}

function Step1({ name, client, description, language, onChange }: Step1Props) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Name your project</h2>
        <p className="text-sm text-muted-foreground">
          Give the engagement a clear, identifiable name.
        </p>
      </div>

      <div className="space-y-3">
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="proj-name">
            Project name <span className="text-destructive">*</span>
          </label>
          <Input
            id="proj-name"
            placeholder="e.g. Acme Corp Market Analysis"
            value={name}
            onChange={(e) => onChange("name", e.target.value)}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="proj-client">
            Client / engagement
          </label>
          <Input
            id="proj-client"
            placeholder="e.g. Acme Corp"
            value={client}
            onChange={(e) => onChange("client", e.target.value)}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="proj-desc">
            Description
          </label>
          <textarea
            id="proj-desc"
            rows={3}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            placeholder="Briefly describe the engagement scope…"
            value={description}
            onChange={(e) => onChange("description", e.target.value)}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="proj-lang">
            Output language
          </label>
          <select
            id="proj-lang"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={language}
            onChange={(e) => onChange("language", e.target.value)}
          >
            {LANGUAGE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

interface Step2Props {
  files: UploadFile[];
  onFilesChange: (files: UploadFile[]) => void;
}

function Step2({ files, onFilesChange }: Step2Props) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Add initial sources</h2>
        <p className="text-sm text-muted-foreground">
          Optional — you can add more sources at any time from the project dashboard.
        </p>
      </div>
      <MultiUploader files={files} onFilesChange={onFilesChange} />
    </div>
  );
}

interface Step3Props {
  modelProfile: string;
  enableDeerFlow: boolean;
  enableHermes: boolean;
  enableMiroFish: boolean;
  onChange: <K extends keyof WizardState>(key: K, value: WizardState[K]) => void;
}

function Step3({
  modelProfile,
  enableDeerFlow,
  enableHermes,
  enableMiroFish,
  onChange,
}: Step3Props) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Configure adapters</h2>
        <p className="text-sm text-muted-foreground">
          Choose the model profile and enable optional tool adapters.
        </p>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="model-profile">
          Model profile
        </label>
        <select
          id="model-profile"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={modelProfile}
          onChange={(e) => onChange("modelProfile", e.target.value)}
        >
          {MODEL_PROFILES.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-medium">Tool adapters</p>
        <AdapterToggle
          label="DeerFlow"
          description="AI research agent — runs autonomous web research queries."
          checked={enableDeerFlow}
          onChange={(v) => onChange("enableDeerFlow", v)}
        />
        <AdapterToggle
          label="Hermes"
          description="Persistent conversational context across sessions."
          checked={enableHermes}
          onChange={(v) => onChange("enableHermes", v)}
        />
        <AdapterToggle
          label="MiroFish"
          description="What-if scenario simulation. Requires explicit confirmation per run."
          checked={enableMiroFish}
          onChange={(v) => onChange("enableMiroFish", v)}
          premium
        />
      </div>
    </div>
  );
}

interface AdapterToggleProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  premium?: boolean;
}

function AdapterToggle({
  label,
  description,
  checked,
  onChange,
  premium,
}: AdapterToggleProps) {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-md border p-3 transition-colors hover:bg-accent">
      <input
        type="checkbox"
        className="mt-0.5 h-4 w-4 accent-primary"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{label}</span>
          {premium && (
            <Badge variant="outline" className="text-xs">
              Premium
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
    </label>
  );
}

interface Step4Props {
  state: WizardState;
  error: string | null;
}

function Step4({ state, error }: Step4Props) {
  const totalFiles = state.files.length;
  const languageLabel =
    LANGUAGE_OPTIONS.find((l) => l.value === state.language)?.label ?? state.language;
  const modelLabel =
    MODEL_PROFILES.find((m) => m.value === state.modelProfile)?.label ??
    state.modelProfile;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Review & create</h2>
        <p className="text-sm text-muted-foreground">
          Confirm the details before creating your project.
        </p>
      </div>

      <div className="space-y-2 rounded-md bg-muted/50 p-4 text-sm">
        <SummaryRow label="Name" value={state.name} />
        {state.client && <SummaryRow label="Client" value={state.client} />}
        {state.description && <SummaryRow label="Description" value={state.description} />}
        <SummaryRow label="Language" value={languageLabel} />
        <SummaryRow label="Sources" value={totalFiles > 0 ? `${totalFiles} file(s) queued` : "None (add later)"} />
        <SummaryRow label="Model profile" value={modelLabel} />
        <SummaryRow
          label="Adapters"
          value={[
            state.enableDeerFlow && "DeerFlow",
            state.enableHermes && "Hermes",
            state.enableMiroFish && "MiroFish",
          ]
            .filter(Boolean)
            .join(", ") || "None"}
        />
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="w-28 shrink-0 text-xs font-medium text-muted-foreground">
        {label}
      </span>
      <span className="text-foreground">{value}</span>
    </div>
  );
}
