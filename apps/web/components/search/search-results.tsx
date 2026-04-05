"use client";

import { useState } from "react";
import type { SearchHit, EvidencePack } from "@/lib/api";
import { buildEvidence } from "@/lib/api";
import { SearchResultCard } from "./search-result-card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";

interface SearchResultsProps {
  hits: SearchHit[];
  query: string;
  workspaceId: string;
}

export function SearchResults({ hits, query, workspaceId }: SearchResultsProps) {
  const [selected, setSelected] = useState<string[]>([]);
  const [evidencePack, setEvidencePack] = useState<EvidencePack | null>(null);
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const kindCounts = hits.reduce<Record<string, number>>((acc, h) => {
    acc[h.kind] = (acc[h.kind] ?? 0) + 1;
    return acc;
  }, {});

  const handleAddEvidence = (hit: SearchHit) => {
    setSelected((prev) =>
      prev.includes(hit.noteId)
        ? prev.filter((id) => id !== hit.noteId)
        : [...prev, hit.noteId]
    );
  };

  const handleBuildEvidence = async () => {
    if (selected.length === 0) return;
    setBuilding(true);
    setError(null);
    const result = await buildEvidence(workspaceId, query, selected).catch(
      () => null
    );
    setBuilding(false);
    if (result?.data) {
      setEvidencePack(result.data);
    } else {
      setError(result?.error ?? "Failed to build evidence pack.");
    }
  };

  if (hits.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-12 text-center">
        <p className="text-sm text-muted-foreground">
          No results for <strong>&ldquo;{query}&rdquo;</strong>.
        </p>
      </div>
    );
  }

  return (
    <div className="flex gap-6">
      {/* Results column */}
      <div className="flex-1 space-y-4">
        {/* Facets */}
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
          <span>{hits.length} results</span>
          {Object.entries(kindCounts).map(([kind, count]) => (
            <span
              key={kind}
              className="rounded bg-secondary px-2 py-0.5 capitalize"
            >
              {kind}: {count}
            </span>
          ))}
        </div>

        <div className="space-y-2">
          {hits.map((hit) => (
            <SearchResultCard
              key={hit.noteId}
              hit={hit}
              query={query}
              onBuildEvidence={handleAddEvidence}
              selected={selected.includes(hit.noteId)}
            />
          ))}
        </div>
      </div>

      {/* Evidence panel */}
      <aside className="w-80 shrink-0 space-y-4">
        <div className="rounded-lg border p-4 space-y-3">
          <h2 className="text-sm font-semibold">Evidence pack</h2>
          {selected.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              Click &ldquo;+ Evidence&rdquo; on results to select passages.
            </p>
          ) : (
            <>
              <p className="text-xs text-muted-foreground">
                {selected.length} note{selected.length !== 1 ? "s" : ""} selected
              </p>
              <Button
                size="sm"
                onClick={handleBuildEvidence}
                disabled={building}
                className="w-full"
              >
                {building ? "Building…" : "Build evidence pack"}
              </Button>
            </>
          )}

          {error && (
            <p className="text-xs text-destructive" role="alert">
              {error}
            </p>
          )}

          {evidencePack && (
            <div className="space-y-3 pt-2">
              <Separator />
              <p className="text-xs text-muted-foreground">
                Assembled {new Date(evidencePack.assembledAt).toLocaleString()}
              </p>
              <ScrollArea className="max-h-96">
                <div className="space-y-3">
                  {evidencePack.citations.map((citation, i) => (
                    <div key={i} className="space-y-1">
                      <p className="text-xs font-medium">{citation.title}</p>
                      <blockquote className="border-l-2 pl-2 text-xs text-muted-foreground italic">
                        &ldquo;{citation.passage}&rdquo;
                      </blockquote>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
