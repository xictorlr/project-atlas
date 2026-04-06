"use client";

import { useEffect, useState } from "react";
import { Cpu, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { type ModelInfo } from "@/lib/api";

// Mock data — replace with getModels() once the API endpoint is available
const MOCK_MODELS: ModelInfo[] = [
  {
    name: "llama3.2:3b",
    size: 2_019_686_400,
    digest: "a80c4f17acd5",
    modifiedAt: new Date().toISOString(),
  },
  {
    name: "mistral:7b",
    size: 4_113_301_504,
    digest: "61e88e884507",
    modifiedAt: new Date().toISOString(),
  },
  {
    name: "qwen2.5:14b",
    size: 9_053_000_000,
    digest: "3b5f40f5f2cf",
    modifiedAt: new Date().toISOString(),
  },
];

function bytesToGb(bytes: number): string {
  return (bytes / 1_073_741_824).toFixed(1);
}

interface ModelSelectorProps {
  value?: string;
  onChange: (modelName: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function ModelSelector({
  value,
  onChange,
  placeholder = "Select model",
  disabled = false,
  className,
}: ModelSelectorProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadModels() {
      setLoading(true);
      try {
        // TODO: replace with real API call
        // const res = await getModels();
        // if (res.success && res.data) setModels(res.data);
        await new Promise((r) => setTimeout(r, 200)); // simulate latency
        setModels(MOCK_MODELS);
      } finally {
        setLoading(false);
      }
    }
    void loadModels();
  }, []);

  const selected = models.find((m) => m.name === value);

  return (
    <div className={cn("relative", className)}>
      <Button
        type="button"
        variant="outline"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label="Select inference model"
        disabled={disabled || loading}
        className="w-full justify-between font-normal"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="flex items-center gap-2 min-w-0">
          <Cpu className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate">
            {loading
              ? "Loading models..."
              : selected
              ? selected.name
              : placeholder}
          </span>
        </span>
        <ChevronDown
          className={cn(
            "ml-2 h-4 w-4 shrink-0 text-muted-foreground transition-transform",
            open && "rotate-180"
          )}
        />
      </Button>

      {open && !loading && (
        <div
          className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-md"
          role="listbox"
          aria-label="Available models"
        >
          {models.length === 0 ? (
            <div className="px-3 py-4 text-sm text-muted-foreground text-center">
              No models installed.
            </div>
          ) : (
            <ul className="max-h-56 overflow-y-auto py-1">
              {models.map((model) => (
                <li
                  key={model.name}
                  role="option"
                  aria-selected={model.name === value}
                  className={cn(
                    "flex cursor-pointer items-center justify-between px-3 py-2 text-sm transition-colors hover:bg-accent",
                    model.name === value && "bg-accent/60"
                  )}
                  onClick={() => {
                    onChange(model.name);
                    setOpen(false);
                  }}
                >
                  <span className="font-medium">{model.name}</span>
                  <span className="ml-4 shrink-0 text-xs text-muted-foreground">
                    {bytesToGb(model.size)} GB
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
