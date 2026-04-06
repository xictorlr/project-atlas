"use client";

import { useEffect, useState } from "react";
import { Cpu, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getModels, type ModelInfo } from "@/lib/api";

interface ApiModel {
  name: string;
  size_gb: number;
  family?: string;
  quantization?: string;
  modified_at?: string;
}

function apiModelToModelInfo(m: ApiModel): ModelInfo {
  return {
    name: m.name,
    size: Math.round(m.size_gb * 1_073_741_824),
    digest: m.quantization ?? "",
    modifiedAt: m.modified_at ?? new Date().toISOString(),
  };
}

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
        const res = await getModels();
        if (res.success && res.data) {
          // API returns { models: [...], total } not a raw array
          const payload = res.data as unknown as { models?: ApiModel[] };
          const list = Array.isArray(payload) ? (payload as ApiModel[]) : payload.models ?? [];
          setModels(list.map(apiModelToModelInfo));
        }
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
