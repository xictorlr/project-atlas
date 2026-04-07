"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { reingestSource } from "@/lib/api";

interface SourceActionsProps {
  workspaceId: string;
  sourceId: string;
  status: string;
  needsReingest?: boolean;
}

/**
 * Inline reingest button shown for sources that previously failed or that
 * landed as a placeholder because the MLX backend was unavailable.
 *
 * The button is hidden when the source is already in a healthy state so the
 * sources table stays uncluttered for the common path.
 */
export function SourceActions({
  workspaceId,
  sourceId,
  status,
  needsReingest,
}: SourceActionsProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const showReingest = status === "failed" || needsReingest === true;
  if (!showReingest) {
    return null;
  }

  const handleClick = () => {
    setError(null);
    startTransition(async () => {
      const res = await reingestSource(workspaceId, sourceId);
      if (!res.success) {
        setError(res.error ?? "Re-ingest failed");
        return;
      }
      router.refresh();
    });
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        size="sm"
        variant="outline"
        disabled={isPending}
        onClick={handleClick}
        className="gap-1.5"
      >
        <RotateCw className={`h-3.5 w-3.5 ${isPending ? "animate-spin" : ""}`} />
        {isPending ? "Re-queuing…" : "Re-ingest"}
      </Button>
      {error && <span className="text-xs text-destructive">{error}</span>}
    </div>
  );
}
